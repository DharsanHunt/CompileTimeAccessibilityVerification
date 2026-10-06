"""Constraint-based tab order auto-repair and diff generator (FR10 stretch)."""

from __future__ import annotations
import difflib
import re
from typing import Dict, List, Tuple, Optional
from .parser import parse_source
from .symbol_table import SymbolTable
from .ast_nodes import Program, Element


class TabOrderAutoRepair:
    def __init__(self, source: str):
        self.original_source = source
        self.program = parse_source(source)
        self.symbols = SymbolTable(self.program)
        self.symbols.build_and_validate()

    def compute_repair(self) -> Tuple[str, str, Dict[str, Optional[int]]]:
        """
        Computes corrected tabindex assignments based on visual layout (y, x).
        Returns: (repaired_source, unified_diff, dict_of_id_to_new_tabindex)
        """
        interactive_elems = [e for e in self.symbols.element_list if e.is_interactive]
        # Sort strictly by visual position (y, x)
        sorted_visual = sorted(interactive_elems, key=lambda e: (e.y, e.x, e.element_id))

        # Build mapping of element_id -> new tabindex (1-based sequence)
        repaired_tabindices: Dict[str, int] = {}
        for idx, elem in enumerate(sorted_visual, start=1):
            repaired_tabindices[elem.element_id] = idx

        # Apply replacements to source code text
        repaired_source = self.original_source

        # For each element, update or insert tabindex
        for elem in self.symbols.element_list:
            elem_id = elem.element_id
            if elem_id not in repaired_tabindices:
                continue

            new_tabindex = repaired_tabindices[elem_id]
            old_tabindex = elem.tabindex

            if old_tabindex == new_tabindex:
                continue

            # Regex search for element pattern with id="elem_id"
            # Replace tabindex=... if exists, else insert before closing paren
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
                # Also check tabindex before id
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
                    # Insert tabindex if was unindexed
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
