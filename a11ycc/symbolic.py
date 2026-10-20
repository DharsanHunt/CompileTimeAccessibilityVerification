"""Symbolic model checking engine using Reduced Ordered Binary Decision Diagrams (ROBDD).

Provides O(polynomial) verification of accessibility state spaces scaling up to
k >= 15 toggles (32,768+ states) with zero external runtime dependencies.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any, Set
from .ast_nodes import Program, Element, ToggleDecl, BoolExpr, Var, Not, And, Or
from .symbol_table import SymbolTable
from .diagnostics import Diagnostic, DiagnosticsReport
from .profiles import AccessibilityProfile, get_profile


class BDDNode:
    """Represents a node in an ROBDD."""
    __slots__ = ("var", "low", "high", "id")

    def __init__(self, node_id: int, var: int, low: int, high: int):
        self.id = node_id
        self.var = var      # Variable index (0-indexed, terminal is -1)
        self.low = low      # Node ID for low branch (var = False)
        self.high = high    # Node ID for high branch (var = True)

    def __repr__(self) -> str:
        if self.id == 0:
            return "BDD(False)"
        if self.id == 1:
            return "BDD(True)"
        return f"BDDNode(id={self.id}, var={self.var}, low={self.low}, high={self.high})"


class BDDManager:
    """Canonical ROBDD Manager with Shannon expansion and ITE memoization.

    Maintains canonical uniqueness: isomorphic subgraphs are guaranteed to share identical IDs.
    """

    def __init__(self, var_names: List[str]):
        # Deterministic variable ordering by sorted toggle name
        self.var_names = list(var_names)
        self.var_to_idx = {name: idx for idx, name in enumerate(self.var_names)}
        self.num_vars = len(self.var_names)

        # Constant terminals: 0 = False, 1 = True
        self.nodes: List[Optional[BDDNode]] = [
            BDDNode(node_id=0, var=self.num_vars, low=0, high=0),
            BDDNode(node_id=1, var=self.num_vars, low=1, high=1),
        ]

        # Unique table: (var, low, high) -> node_id
        self.unique_table: Dict[Tuple[int, int, int], int] = {}

        # Computed cache for ITE and operations: (op, arg1, arg2, arg3) -> result_node_id
        self.computed_cache: Dict[Tuple[Any, ...], int] = {}

    @property
    def false(self) -> int:
        return 0

    @property
    def true(self) -> int:
        return 1

    def var(self, name: str) -> int:
        """Returns the BDD node representing the single variable `name`."""
        if name not in self.var_to_idx:
            raise KeyError(f"Variable '{name}' not found in BDD manager ordering.")
        var_idx = self.var_to_idx[name]
        return self.get_node(var_idx, self.false, self.true)

    def get_node(self, var: int, low: int, high: int) -> int:
        """Returns the canonical node for (var, low, high) with reduction rules."""
        # Reduction rule 1: redundant node elimination (low == high)
        if low == high:
            return low

        key = (var, low, high)
        if key in self.unique_table:
            return self.unique_table[key]

        new_id = len(self.nodes)
        node = BDDNode(node_id=new_id, var=var, low=low, high=high)
        self.nodes.append(node)
        self.unique_table[key] = new_id
        return new_id

    def top_var(self, node_id: int) -> int:
        return self.nodes[node_id].var

    def ite(self, f: int, g: int, h: int) -> int:
        """If-Then-Else operator: (f and g) or (not f and h).

        Fundamental building block for all boolean operations in ROBDD.
        """
        # Terminal reductions
        if f == self.true:
            return g
        if f == self.false:
            return h
        if g == h:
            return g
        if g == self.true and h == self.false:
            return f

        cache_key = ("ite", f, g, h)
        if cache_key in self.computed_cache:
            return self.computed_cache[cache_key]

        # Shannon expansion on lowest variable index
        x = min(self.top_var(f), self.top_var(g), self.top_var(h))

        f0, f1 = self._cofactor(f, x)
        g0, g1 = self._cofactor(g, x)
        h0, h1 = self._cofactor(h, x)

        low = self.ite(f0, g0, h0)
        high = self.ite(f1, g1, h1)

        result = self.get_node(x, low, high)
        self.computed_cache[cache_key] = result
        return result

    def _cofactor(self, node_id: int, var_idx: int) -> Tuple[int, int]:
        """Returns (f|_{var=0}, f|_{var=1})."""
        node = self.nodes[node_id]
        if node.var > var_idx:
            # Variable does not appear above or at this node
            return node_id, node_id
        if node.var == var_idx:
            return node.low, node.high
        raise ValueError("Variable ordering invariant violated in cofactor.")

    def bdd_not(self, f: int) -> int:
        """Computes NOT f."""
        return self.ite(f, self.false, self.true)

    def bdd_and(self, f: int, g: int) -> int:
        """Computes f AND g."""
        return self.ite(f, g, self.false)

    def bdd_or(self, f: int, g: int) -> int:
        """Computes f OR g."""
        return self.ite(f, self.true, g)

    def bdd_xor(self, f: int, g: int) -> int:
        """Computes f XOR g."""
        return self.ite(f, self.bdd_not(g), g)

    def bdd_implies(self, f: int, g: int) -> int:
        """Computes f -> g."""
        return self.ite(f, g, self.true)

    def bdd_equiv(self, f: int, g: int) -> int:
        """Computes f <-> g."""
        return self.ite(f, g, self.bdd_not(g))

    def substitute_flip(self, node_id: int, var_idx: int) -> int:
        """Computes f with variable `var_idx` inverted (x_i -> not x_i)."""
        node = self.nodes[node_id]
        if node.var > var_idx:
            return node_id

        cache_key = ("flip", node_id, var_idx)
        if cache_key in self.computed_cache:
            return self.computed_cache[cache_key]

        if node.var == var_idx:
            # Swap low and high branches
            result = self.get_node(var_idx, node.high, node.low)
        else:
            new_low = self.substitute_flip(node.low, var_idx)
            new_high = self.substitute_flip(node.high, var_idx)
            result = self.get_node(node.var, new_low, new_high)

        self.computed_cache[cache_key] = result
        return result

    def is_satisfiable(self, node_id: int) -> bool:
        """Formula is SAT iff its ROBDD is not the 0 terminal."""
        return node_id != self.false

    def is_tautology(self, node_id: int) -> bool:
        """Formula is valid iff its ROBDD is the 1 terminal."""
        return node_id == self.true

    def count_sat(self, node_id: int, num_vars: Optional[int] = None) -> int:
        """Computes the exact number of satisfying assignments out of 2^num_vars."""
        if num_vars is None:
            num_vars = self.num_vars

        memo: Dict[Tuple[int, int], int] = {}

        def _count(curr_id: int, curr_var: int) -> int:
            if curr_id == self.false:
                return 0
            if curr_id == self.true:
                return 1 << (num_vars - curr_var)

            key = (curr_id, curr_var)
            if key in memo:
                return memo[key]

            node = self.nodes[curr_id]
            # Account for skipped variables in BDD ordering
            skipped = node.var - curr_var
            factor = 1 << skipped

            cnt_low = _count(node.low, node.var + 1)
            cnt_high = _count(node.high, node.var + 1)
            res = factor * (cnt_low + cnt_high)
            memo[key] = res
            return res

        return _count(node_id, 0)

    def any_sat(self, node_id: int) -> Optional[Dict[str, bool]]:
        """Extracts a single satisfying boolean assignment (counterexample), if any."""
        if node_id == self.false:
            return None

        assignment: Dict[str, bool] = {name: False for name in self.var_names}
        curr = node_id
        while curr != self.true:
            node = self.nodes[curr]
            var_name = self.var_names[node.var]
            if node.low != self.false:
                assignment[var_name] = False
                curr = node.low
            else:
                assignment[var_name] = True
                curr = node.high

        return assignment


def ast_expr_to_bdd(manager: BDDManager, expr: Optional[BoolExpr]) -> int:
    """Translates an AST BoolExpr into an ROBDD node."""
    if expr is None:
        return manager.true
    if isinstance(expr, Var):
        return manager.var(expr.name)
    if isinstance(expr, Not):
        return manager.bdd_not(ast_expr_to_bdd(manager, expr.inner))
    if isinstance(expr, And):
        return manager.bdd_and(ast_expr_to_bdd(manager, expr.left), ast_expr_to_bdd(manager, expr.right))
    if isinstance(expr, Or):
        return manager.bdd_or(ast_expr_to_bdd(manager, expr.left), ast_expr_to_bdd(manager, expr.right))
    raise TypeError(f"Unknown BoolExpr node type: {type(expr)}")


class SymbolicAccessibilityAnalyzer:
    """Symbolic model checker for A11yCC.

    Verifies accessibility invariants over 2^k state spaces symbolically
    using canonical Reduced Ordered Binary Decision Diagrams.
    """

    def __init__(
        self,
        program: Program,
        symbol_table: SymbolTable,
        profile: Optional[AccessibilityProfile] = None,
    ):
        self.program = program
        self.symbols = symbol_table
        self.profile = profile or get_profile(program.profile)
        self.toggle_names = sorted([t.name for t in program.toggles])
        self.bdd = BDDManager(self.toggle_names)

        # Precompute symbolic visibility BDD for every element
        self.elem_vis_bdd: Dict[str, int] = {}
        self._compute_symbolic_visibility()

    def _compute_symbolic_visibility(self) -> None:
        for elem in self.symbols.element_list:
            cond = ast_expr_to_bdd(self.bdd, elem.show_when)
            for ancestor in self.symbols.get_ancestors(elem.element_id):
                if ancestor.show_when is not None:
                    ancestor_cond = ast_expr_to_bdd(self.bdd, ancestor.show_when)
                    cond = self.bdd.bdd_and(cond, ancestor_cond)
            self.elem_vis_bdd[elem.element_id] = cond

    def analyze(self) -> DiagnosticsReport:
        report = DiagnosticsReport()

        # Step 1: Missing Label Check (FR6 - WCAG 4.1.2)
        for elem in self.symbols.element_list:
            vis_node = self.elem_vis_bdd[elem.element_id]
            if not self.bdd.is_satisfiable(vis_node):
                # Element is never reachable/visible in any state
                continue

            if elem.kind in ("Button", "Input"):
                if not elem.label or not elem.label.strip():
                    sat_state = self.bdd.any_sat(vis_node)
                    report.add(Diagnostic(
                        rule="MissingLabel",
                        wcag="4.1.2",
                        element_id=elem.element_id,
                        state_path={"state": sat_state},
                        message=(
                            f"Interactive element '{elem.element_id}' of kind '{elem.kind}' is missing a required "
                            f"accessible 'label' attribute in reachable state {sat_state}."
                        ),
                        severity="error",
                        pos=elem.pos,
                    ))

            if self.profile.require_text_labels and elem.kind == "Text":
                if not elem.label or not elem.label.strip():
                    sat_state = self.bdd.any_sat(vis_node)
                    report.add(Diagnostic(
                        rule="MissingTextContent",
                        wcag="4.1.2",
                        element_id=elem.element_id,
                        state_path={"state": sat_state},
                        message=f"Text element '{elem.element_id}' is missing a 'label' attribute under profile '{self.profile.name}' in state {sat_state}.",
                        severity="warning",
                        pos=elem.pos,
                    ))

        # Step 2: Focus Order Mismatch Check (FR5 - WCAG 2.4.3)
        interactive_elems = [e for e in self.symbols.element_list if e.is_interactive]
        # Check pairwise focus/visual order divergences
        for i in range(len(interactive_elems)):
            for j in range(len(interactive_elems)):
                if i == j:
                    continue
                e1, e2 = interactive_elems[i], interactive_elems[j]
                # Visual order precedence: e1 < e2
                e1_vis_before_e2 = (e1.y, e1.x, e1.element_id) < (e2.y, e2.x, e2.element_id)
                if not e1_vis_before_e2:
                    continue

                # Tabindex order precedence: does e2 precede e1 in tab order?
                e2_tabs_before_e1 = False
                t1, t2 = e1.tabindex or 0, e2.tabindex or 0
                if t1 > 0 and t2 > 0:
                    if t2 < t1:
                        e2_tabs_before_e1 = True
                elif t1 == 0 and t2 > 0:
                    e2_tabs_before_e1 = True  # positive tabindex visited before 0

                if e2_tabs_before_e1:
                    # Conflict exists if both e1 and e2 are simultaneously visible
                    conflict = self.bdd.bdd_and(
                        self.elem_vis_bdd[e1.element_id],
                        self.elem_vis_bdd[e2.element_id],
                    )
                    if self.bdd.is_satisfiable(conflict):
                        sat_state = self.bdd.any_sat(conflict)
                        report.add(Diagnostic(
                            rule="FocusOrderMismatch",
                            wcag="2.4.3",
                            element_id=e2.element_id,
                            state_path={"state": sat_state},
                            message=(
                                f"Keyboard focus order diverges from visual reading order in state {sat_state}. "
                                f"Element '{e2.element_id}' (tabindex={e2.tabindex}) jumps ahead of visual predecessor '{e1.element_id}'."
                            ),
                            severity="error",
                            pos=e2.pos,
                        ))

        # Step 3: Transition Analysis (Potential Focus Trap / Vanishing Focus) (FR7 - WCAG 2.4.3, 2.1.2)
        for elem in interactive_elems:
            vis_a = self.elem_vis_bdd[elem.element_id]
            if not self.bdd.is_satisfiable(vis_a):
                continue

            for toggle_name in self.toggle_names:
                var_idx = self.bdd.var_to_idx[toggle_name]
                # Vanishes condition: element is visible in state s, but NOT visible when toggle flips
                vis_b = self.bdd.substitute_flip(vis_a, var_idx)
                vanishes = self.bdd.bdd_and(vis_a, self.bdd.bdd_not(vis_b))
                if not self.bdd.is_satisfiable(vanishes):
                    continue

                fallback_id = elem.focus_fallback
                if not fallback_id:
                    # Trap: vanishes with no fallback declared
                    sat_state_a = self.bdd.any_sat(vanishes)
                    sat_state_b = dict(sat_state_a)
                    sat_state_b[toggle_name] = not sat_state_a[toggle_name]
                    report.add(Diagnostic(
                        rule="PotentialFocusTrap",
                        wcag="2.4.3, 2.1.2",
                        element_id=elem.element_id,
                        state_path={"from": sat_state_a, "to": sat_state_b},
                        message=(
                            f"'{elem.element_id}' is focused and interactive in state {sat_state_a}; "
                            f"on transition to {sat_state_b} it disappears with no focus_fallback declared."
                        ),
                        severity="error",
                        pos=elem.pos,
                    ))
                else:
                    # Fallback declared: check if fallback is visible in destination state
                    fallback_vis_b = self.bdd.substitute_flip(self.elem_vis_bdd[fallback_id], var_idx)
                    trap_condition = self.bdd.bdd_and(vanishes, self.bdd.bdd_not(fallback_vis_b))
                    if self.bdd.is_satisfiable(trap_condition):
                        sat_state_a = self.bdd.any_sat(trap_condition)
                        sat_state_b = dict(sat_state_a)
                        sat_state_b[toggle_name] = not sat_state_a[toggle_name]
                        report.add(Diagnostic(
                            rule="PotentialFocusTrap",
                            wcag="2.4.3, 2.1.2",
                            element_id=elem.element_id,
                            state_path={"from": sat_state_a, "to": sat_state_b},
                            message=(
                                f"'{elem.element_id}' disappears on transition from {sat_state_a} to {sat_state_b}; "
                                f"its declared focus_fallback '{fallback_id}' is not visible in the new state."
                            ),
                            severity="error",
                            pos=elem.pos,
                        ))

        report.sort_deterministic()
        return report
