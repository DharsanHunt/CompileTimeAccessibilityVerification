"""Unit tests for Reduced Ordered Binary Decision Diagrams (ROBDD) and Symbolic Model Checking."""

import unittest
from a11ycc.symbolic import BDDManager, SymbolicAccessibilityAnalyzer
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable


class TestROBDDEngine(unittest.TestCase):
    def test_canonical_reduction_and_uniqueness(self):
        bdd = BDDManager(["a", "b", "c"])
        # Reduction rule 1: get_node(var, x, x) must reduce directly to x
        node = bdd.get_node(0, bdd.true, bdd.true)
        self.assertEqual(node, bdd.true)

        # Reduction rule 2: isomorphic nodes must share identical ID
        n1 = bdd.get_node(1, bdd.false, bdd.true)
        n2 = bdd.get_node(1, bdd.false, bdd.true)
        self.assertEqual(n1, n2)

    def test_boolean_operations_via_ite(self):
        bdd = BDDManager(["x", "y"])
        x = bdd.var("x")
        y = bdd.var("y")

        # Law of excluded middle: x OR NOT x == 1
        not_x = bdd.bdd_not(x)
        self.assertEqual(bdd.bdd_or(x, not_x), bdd.true)

        # Law of non-contradiction: x AND NOT x == 0
        self.assertEqual(bdd.bdd_and(x, not_x), bdd.false)

        # De Morgan's Law: NOT (x AND y) == (NOT x) OR (NOT y)
        left = bdd.bdd_not(bdd.bdd_and(x, y))
        right = bdd.bdd_or(bdd.bdd_not(x), bdd.bdd_not(y))
        self.assertEqual(left, right)

        # XOR property: x XOR y == (x AND NOT y) OR (NOT x AND y)
        xor_direct = bdd.bdd_xor(x, y)
        xor_expanded = bdd.bdd_or(
            bdd.bdd_and(x, bdd.bdd_not(y)),
            bdd.bdd_and(bdd.bdd_not(x), y),
        )
        self.assertEqual(xor_direct, xor_expanded)

    def test_satisfying_count_exponential_scale(self):
        # Scale to 15 variables (2^15 = 32,768 states)
        varnames = [f"toggle_{i}" for i in range(15)]
        bdd = BDDManager(varnames)

        # Formula True over 15 vars has exactly 2^15 = 32,768 states
        self.assertEqual(bdd.count_sat(bdd.true), 32768)
        self.assertEqual(bdd.count_sat(bdd.false), 0)

        # A single variable constraint t_0 = True leaves 2^14 = 16,384 states
        t0 = bdd.var("toggle_0")
        self.assertEqual(bdd.count_sat(t0), 16384)

        # Conjunction of 3 variables leaves 2^12 = 4,096 states
        t1 = bdd.var("toggle_1")
        t2 = bdd.var("toggle_2")
        t0_1_2 = bdd.bdd_and(t0, bdd.bdd_and(t1, t2))
        self.assertEqual(bdd.count_sat(t0_1_2), 4096)

    def test_variable_flip_substitution(self):
        bdd = BDDManager(["a", "b"])
        a = bdd.var("a")
        # Flip variable 'a' -> should equal NOT a
        flipped = bdd.substitute_flip(a, bdd.var_to_idx["a"])
        self.assertEqual(flipped, bdd.bdd_not(a))


class TestSymbolicAccessibilityAnalyzer(unittest.TestCase):
    def test_clean_program_symbolic(self):
        source = """
        toggle sidebarOpen = false;

        Container(id="root", x=0, y=0) {
          Button(id="menu-btn", x=0, y=0, label="Open menu", tabindex=1);
          Group(id="sidebar", x=0, y=40, show_when=sidebarOpen) {
            Button(id="close-btn", x=0, y=40, label="Close menu",
                   tabindex=2, focus_fallback="menu-btn");
            Text(id="sidebar-title", x=0, y=60, label="Navigation");
          }
          Text(id="main-heading", x=100, y=0, label="Welcome");
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = SymbolicAccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()
        self.assertFalse(report.has_errors, f"Unexpected errors: {report.to_json()}")

    def test_focus_trap_detected_symbolic(self):
        source = """
        toggle modalOpen = true;

        Container(id="root", x=0, y=0) {
          Button(id="open-modal", x=0, y=0, label="Open Modal");
          Group(id="modal", x=50, y=50, show_when=modalOpen) {
            Button(id="modal-close", x=50, y=50, label="Close");
          }
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = SymbolicAccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()
        self.assertTrue(report.has_errors)
        traps = [d for d in report.diagnostics if d.rule == "PotentialFocusTrap"]
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].element_id, "modal-close")

    def test_large_toggle_dashboard_scaling(self):
        # 8 toggles (256 states) - verifies scaling beyond NFR1 k=6 bound!
        toggles = "\n".join([f"toggle t_{i} = false;" for i in range(8)])
        source = f"""
        {toggles}
        Container(id="root", x=0, y=0) {{
          Button(id="btn-main", x=0, y=0, label="Dashboard Main");
          Group(id="panel", x=100, y=100, show_when=t_0 && t_1 && t_2) {{
            Button(id="btn-sub", x=100, y=100, label="Sub Action", focus_fallback="btn-main");
          }}
        }}
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        # Verify symbol table with max_toggles cap lifted for symbolic
        symbols.build_and_validate(max_toggles=16)
        analyzer = SymbolicAccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()
        self.assertFalse(report.has_errors)


if __name__ == "__main__":
    unittest.main()
