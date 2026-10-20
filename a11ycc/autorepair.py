"""Automatic repair engine for accessibility defects in A11yCC DSL programs.

Provides 1-click semantic repairs for:
1. FocusOrderMismatch (FR5 / WCAG 2.4.3) - Align tabindex to visual reading order
2. MissingLabel (FR6 / WCAG 4.1.2) - Synthesize human-readable accessible names
3. PotentialFocusTrap (FR7 / WCAG 2.1.2) - Inject or redirect focus_fallback anchors
4. UndeclaredToggle - Declare missing state toggle variables
"""

from __future__ import annotations
import difflib
import re
from typing import Dict, List, Tuple, Optional, Set
from .parser import parse_source, ParseError
from .symbol_table import SymbolTable, SemanticError
from .ast_nodes import Program, Element
from .analyzer import AccessibilityAnalyzer


class A11yAutoRepair:
    """Multi-defect automated repair engine."""

    def __init__(self, source: str):
        self.original_source = source

    def compute_repair(self, max_iterations: int = 5) -> Tuple[str, str, List[str]]:
        """Iteratively repairs all detected syntax, semantic, and accessibility defects.

        Returns: (repaired_source, unified_diff, list_of_applied_repairs)
        """
        curr_source = self.original_source
        applied_repairs: List[str] = []

        for _ in range(max_iterations):
            # 1. Check for undeclared toggle variables
            try:
                prog = parse_source(curr_source)
                symbols = SymbolTable(prog)
                symbols.build_and_validate(max_toggles=20)
            except SemanticError as se:
                # Catch "Undefined toggle variable 'varName'"
                undef_match = re.search(r"Undefined toggle variable '([a-zA-Z0-9_-]+)'", se.message)
                if undef_match:
                    var_name = undef_match.group(1)
                    curr_source = f"toggle {var_name} = false;\n" + curr_source
                    applied_repairs.append(f"Declared missing toggle state: 'toggle {var_name} = false;'")
                    continue
                else:
                    break
            except ParseError:
                break

            # 2. Analyze accessibility rules
            analyzer = AccessibilityAnalyzer(prog, symbols)
            report = analyzer.analyze()
            if not report.has_errors:
                break

            step_applied = False

            # Fix 1: Missing Labels (FR6)
            missing_label_diags = [d for d in report.diagnostics if d.rule == "MissingLabel"]
            for d in missing_label_diags:
                elem_id = d.element_id
                elem = symbols.elements.get(elem_id)
                kind = elem.kind if elem else "Button"
                # Generate clean human-readable label from ID
                clean_name = re.sub(r"[-_]+", " ", elem_id).capitalize()
                new_label = f"{clean_name} {kind.lower()}"

                # Inject label="..." into element
                elem_pat = re.compile(rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*?)(\))', re.DOTALL)
                if elem_pat.search(curr_source):
                    curr_source = elem_pat.sub(rf'\g<1>, label="{new_label}"\g<2>', curr_source, count=1)
                    applied_repairs.append(f"Synthesized accessible label for #{elem_id}: \"{new_label}\"")
                    step_applied = True

            # Fix 2: Focus Order Mismatch (FR5)
            mismatch_diags = [d for d in report.diagnostics if d.rule == "FocusOrderMismatch"]
            if mismatch_diags:
                interactive_elems = [e for e in symbols.element_list if e.is_interactive]
                sorted_visual = sorted(interactive_elems, key=lambda e: (e.y, e.x, e.element_id))
                for idx, elem in enumerate(sorted_visual, start=1):
                    elem_id = elem.element_id
                    if elem.tabindex != idx:
                        pat_tabindex = re.compile(rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*?)\btabindex\s*=\s*\d+', re.DOTALL)
                        if pat_tabindex.search(curr_source):
                            curr_source = pat_tabindex.sub(rf'\g<1>tabindex={idx}', curr_source, count=1)
                            step_applied = True
                        else:
                            pat_elem = re.compile(rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*)(\))', re.DOTALL)
                            curr_source = pat_elem.sub(rf'\g<1>, tabindex={idx}\g<2>', curr_source, count=1)
                            step_applied = True
                if step_applied:
                    applied_repairs.append("Re-sequenced tabindex order (1, 2, 3...) to match visual (y, x) flow")

            # Fix 3: Potential Focus Traps (FR7)
            trap_diags = [d for d in report.diagnostics if d.rule == "PotentialFocusTrap"]
            for d in trap_diags:
                elem_id = d.element_id
                elem = symbols.elements.get(elem_id)
                if not elem:
                    continue

                # Find a persistent interactive element outside conditional groups to serve as fallback
                fallback_target = None
                for candidate in symbols.element_list:
                    if candidate.is_interactive and candidate.element_id != elem_id and candidate.show_when is None:
                        fallback_target = candidate.element_id
                        break

                if not fallback_target:
                    # Fallback to the first interactive element
                    for candidate in symbols.element_list:
                        if candidate.is_interactive and candidate.element_id != elem_id:
                            fallback_target = candidate.element_id
                            break

                if fallback_target:
                    # Replace existing focus_fallback or insert new one
                    pat_existing = re.compile(rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*?)\bfocus_fallback\s*=\s*"[^"]*"', re.DOTALL)
                    if pat_existing.search(curr_source):
                        curr_source = pat_existing.sub(rf'\g<1>focus_fallback="{fallback_target}"', curr_source, count=1)
                        applied_repairs.append(f"Redirected focus_fallback on #{elem_id} to persistent anchor #{fallback_target}")
                        step_applied = True
                    else:
                        pat_insert = re.compile(rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*)(\))', re.DOTALL)
                        curr_source = pat_insert.sub(rf'\g<1>, focus_fallback="{fallback_target}"\g<2>', curr_source, count=1)
                        applied_repairs.append(f"Injected focus_fallback=\"{fallback_target}\" on vanishing element #{elem_id}")
                        step_applied = True

            if not step_applied:
                break

        diff = self._generate_diff(self.original_source, curr_source)
        return curr_source, diff, applied_repairs

    def _generate_diff(self, original: str, repaired: str) -> str:
        orig_lines = original.splitlines(keepends=True)
        rep_lines = repaired.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines,
            rep_lines,
            fromfile="original.dsl",
            tofile="repaired.dsl",
            lineterm=""
        ))
        return "".join(diff_lines)


class TabOrderAutoRepair:
    """Maintains backward compatibility with original FR10 TabOrderAutoRepair API."""

    def __init__(self, source: str):
        self.original_source = source
        self.program = parse_source(source)
        self.symbols = SymbolTable(self.program)
        self.symbols.build_and_validate(max_toggles=20)

    def compute_repair(self) -> Tuple[str, str, Dict[str, Optional[int]]]:
        interactive_elems = [e for e in self.symbols.element_list if e.is_interactive]
        sorted_visual = sorted(interactive_elems, key=lambda e: (e.y, e.x, e.element_id))

        repaired_tabindices: Dict[str, int] = {}
        for idx, elem in enumerate(sorted_visual, start=1):
            repaired_tabindices[elem.element_id] = idx

        repaired_source = self.original_source

        for elem in self.symbols.element_list:
            elem_id = elem.element_id
            if elem_id not in repaired_tabindices:
                continue

            new_tabindex = repaired_tabindices[elem_id]
            old_tabindex = elem.tabindex

            if old_tabindex == new_tabindex:
                continue

            pattern_with_tabindex = re.compile(
                rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*?)\btabindex\s*=\s*\d+',
                re.DOTALL
            )
            if pattern_with_tabindex.search(repaired_source):
                repaired_source = pattern_with_tabindex.sub(
                    rf'\g<1>tabindex={new_tabindex}',
                    repaired_source,
                    count=1
                )
            else:
                pattern_tabindex_first = re.compile(
                    rf'\btabindex\s*=\s*\d+([^)]*?id\s*=\s*"{re.escape(elem_id)}")',
                    re.DOTALL
                )
                if pattern_tabindex_first.search(repaired_source):
                    repaired_source = pattern_tabindex_first.sub(
                        rf'tabindex={new_tabindex}\g<1>',
                        repaired_source,
                        count=1
                    )
                else:
                    pattern_elem = re.compile(
                        rf'(id\s*=\s*"{re.escape(elem_id)}"[^)]*)(\))',
                        re.DOTALL
                    )
                    repaired_source = pattern_elem.sub(
                        rf'\g<1>, tabindex={new_tabindex}\g<2>',
                        repaired_source,
                        count=1
                    )

        diff = self._generate_diff(self.original_source, repaired_source)
        return repaired_source, diff, repaired_tabindices

    def _generate_diff(self, original: str, repaired: str) -> str:
        orig_lines = original.splitlines(keepends=True)
        rep_lines = repaired.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(
            orig_lines,
            rep_lines,
            fromfile="original.dsl",
            tofile="repaired.dsl",
            lineterm=""
        ))
        return "".join(diff_lines)
