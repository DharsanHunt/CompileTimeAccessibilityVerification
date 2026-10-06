"""State-space accessibility analysis engine for Kana-Forge."""

from __future__ import annotations
import math
from typing import Dict, List, Set, Tuple, Optional
from .ast_nodes import Program, Element
from .symbol_table import SymbolTable
from .state_space import State, Transition, StateSpace
from .diagnostics import Diagnostic, DiagnosticsReport
from .profiles import AccessibilityProfile, get_profile


class AccessibilityAnalyzer:
    def __init__(self, program: Program, symbol_table: SymbolTable, profile: Optional[AccessibilityProfile] = None):
        self.program = program
        self.symbols = symbol_table
        self.profile = profile or get_profile(program.profile)
        self.state_space = StateSpace(program.toggles)

    def analyze(self) -> DiagnosticsReport:
        report = DiagnosticsReport()

        # Step 1: Precompute visibility per state
        # state -> set of visible element IDs
        state_visible: Dict[State, Set[str]] = {}
        state_visible_elements: Dict[State, List[Element]] = {}

        for state in self.state_space.states:
            env = state.to_dict()
            vis_set: Set[str] = set()
            vis_list: List[Element] = []

            for elem in self.symbols.element_list:
                if self._is_element_visible_in_state(elem, env):
                    vis_set.add(elem.element_id)
                    vis_list.append(elem)

            state_visible[state] = vis_set
            state_visible_elements[state] = vis_list

        # Step 2: Per-state static accessibility analysis
        for state in self.state_space.states:
            vis_elems = state_visible_elements[state]
            self._verify_state_static(state, vis_elems, report)

        # Step 3: Transition analysis (potential focus traps / vanishing focus)
        for trans in self.state_space.transitions:
            self._verify_transition(trans, state_visible, report)

        report.sort_deterministic()
        return report

    def _is_element_visible_in_state(self, elem: Element, env: Dict[str, bool]) -> bool:
        # Check element's own show_when condition
        if elem.show_when is not None:
            if not elem.show_when.evaluate(env):
                return False

        # Check all ancestors' show_when conditions
        for ancestor in self.symbols.get_ancestors(elem.element_id):
            if ancestor.show_when is not None:
                if not ancestor.show_when.evaluate(env):
                    return False

        return True

    def _verify_state_static(self, state: State, vis_elems: List[Element], report: DiagnosticsReport) -> None:
        env = state.to_dict()

        # 1. Missing Label Check (FR6 - WCAG 4.1.2)
        for elem in vis_elems:
            if elem.kind in ("Button", "Input"):
                if not elem.label or not elem.label.strip():
                    report.add(Diagnostic(
                        rule="MissingLabel",
                        wcag="4.1.2",
                        element_id=elem.element_id,
                        state_path={"state": env},
                        message=f"Interactive element '{elem.element_id}' of kind '{elem.kind}' is missing a required accessible 'label' attribute in state {state}.",
                        severity="error",
                        pos=elem.pos,
                    ))

            # Profile-specific check for screen-reader-first
            if self.profile.require_text_labels and elem.kind == "Text":
                if not elem.label or not elem.label.strip():
                    report.add(Diagnostic(
                        rule="MissingTextContent",
                        wcag="4.1.2",
                        element_id=elem.element_id,
                        state_path={"state": env},
                        message=f"Text element '{elem.element_id}' is missing a 'label' attribute under profile '{self.profile.name}' in state {state}.",
                        severity="warning",
                        pos=elem.pos,
                    ))

        # 2. Focus Order Mismatch Check (FR5 - WCAG 2.4.3)
        # Interactive elements in this state:
        interactive_elems = [e for e in vis_elems if e.is_interactive]
        if not interactive_elems:
            return

        # Visual reading order: sort by y (top-to-bottom), then x (left-to-right)
        visual_order = sorted(interactive_elems, key=lambda e: (e.y, e.x, e.element_id))
        visual_ids = [e.element_id for e in visual_order]

        # Computed focus order:
        # Positive tabindex (1, 2, 3...) sorted by tabindex ascending, ties broken by visual order (y, x)
        # Unindexed / tabindex 0 sorted by visual order (y, x)
        pos_tabindex_elems = [e for e in interactive_elems if e.tabindex is not None and e.tabindex > 0]
        pos_tabindex_elems_sorted = sorted(pos_tabindex_elems, key=lambda e: (e.tabindex, e.y, e.x, e.element_id))

        zero_or_unindexed_elems = [e for e in interactive_elems if e.tabindex is None or e.tabindex == 0]
        zero_or_unindexed_sorted = sorted(zero_or_unindexed_elems, key=lambda e: (e.y, e.x, e.element_id))

        focus_order = pos_tabindex_elems_sorted + zero_or_unindexed_sorted
        focus_ids = [e.element_id for e in focus_order]

        if focus_ids != visual_ids:
            # Find first mismatched element
            first_mismatched_id = None
            first_mismatched_pos = None
            for f_id, v_id in zip(focus_ids, visual_ids):
                if f_id != v_id:
                    first_mismatched_id = f_id
                    elem = self.symbols.elements.get(f_id)
                    first_mismatched_pos = elem.pos if elem else None
                    break
            if not first_mismatched_id and len(focus_ids) != len(visual_ids):
                first_mismatched_id = focus_ids[0] if focus_ids else visual_ids[0]

            report.add(Diagnostic(
                rule="FocusOrderMismatch",
                wcag="2.4.3",
                element_id=first_mismatched_id,
                state_path={"state": env},
                message=(
                    f"Keyboard focus order diverges from visual reading order in state {state}. "
                    f"Expected visual sequence: {visual_ids}, but computed tab focus sequence is: {focus_ids}."
                ),
                severity="error",
                pos=first_mismatched_pos,
            ))

        # Profile-specific check for switch-access-first (spatial jump distance)
        if self.profile.max_switch_jump_distance is not None and len(focus_order) > 1:
            for i in range(len(focus_order) - 1):
                e1, e2 = focus_order[i], focus_order[i + 1]
                dist = math.hypot(e2.x - e1.x, e2.y - e1.y)
                if dist > self.profile.max_switch_jump_distance:
                    report.add(Diagnostic(
                        rule="ExcessiveSwitchJumpDistance",
                        wcag="2.4.3",
                        element_id=e2.element_id,
                        state_path={"state": env},
                        message=(
                            f"Large spatial distance ({dist:.1f}px > {self.profile.max_switch_jump_distance}px) "
                            f"between consecutive focus elements '{e1.element_id}' and '{e2.element_id}' in state {state}."
                        ),
                        severity="warning",
                        pos=e2.pos,
                    ))

    def _verify_transition(
        self,
        trans: Transition,
        state_visible: Dict[State, Set[str]],
        report: DiagnosticsReport,
    ) -> None:
        s_a = trans.from_state
        s_b = trans.to_state
        vis_a = state_visible[s_a]
        vis_b = state_visible[s_b]

        vanished_ids = vis_a - vis_b
        if not vanished_ids:
            return

        for elem_id in sorted(vanished_ids):
            elem = self.symbols.elements[elem_id]
            # Only interactive elements hold user focus and risk losing it
            if not elem.is_interactive:
                continue

            fallback_target = elem.focus_fallback
            if not fallback_target:
                report.add(Diagnostic(
                    rule="PotentialFocusTrap",
                    wcag="2.4.3, 2.1.2",
                    element_id=elem.element_id,
                    state_path={"from": s_a.to_dict(), "to": s_b.to_dict()},
                    message=(
                        f"'{elem.element_id}' is focused and interactive in state {s_a}; "
                        f"on transition to {s_b} it disappears with no focus_fallback declared."
                    ),
                    severity="error",
                    pos=elem.pos,
                ))
            elif fallback_target not in vis_b:
                report.add(Diagnostic(
                    rule="PotentialFocusTrap",
                    wcag="2.4.3, 2.1.2",
                    element_id=elem.element_id,
                    state_path={"from": s_a.to_dict(), "to": s_b.to_dict()},
                    message=(
                        f"'{elem.element_id}' disappears on transition from {s_a} to {s_b}; "
                        f"its declared focus_fallback '{fallback_target}' is not visible in the new state."
                    ),
                    severity="error",
                    pos=elem.pos,
                ))
