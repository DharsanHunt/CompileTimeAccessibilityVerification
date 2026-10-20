"""Unit tests for Tab Order Auto-Repair (FR10 stretch)."""

import unittest
from a11ycc.autorepair import TabOrderAutoRepair
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable
from a11ycc.analyzer import AccessibilityAnalyzer


class TestAutoRepair(unittest.TestCase):
    def test_repair_scrambled_tabindex(self):
        buggy_source = """Container(id="root", x=0, y=0) {
  Button(id="btn1", x=0, y=0, label="First", tabindex=3);
  Button(id="btn2", x=0, y=50, label="Second", tabindex=1);
  Button(id="btn3", x=0, y=100, label="Third", tabindex=2);
}"""
        repairer = TabOrderAutoRepair(buggy_source)
        repaired_source, diff_text, tab_map = repairer.compute_repair()

        self.assertIn("-  Button(id=\"btn1\", x=0, y=0, label=\"First\", tabindex=3);", diff_text)
        self.assertIn("+  Button(id=\"btn1\", x=0, y=0, label=\"First\", tabindex=1);", diff_text)
        self.assertEqual(tab_map, {"btn1": 1, "btn2": 2, "btn3": 3})

        # Verify the repaired program produces 0 focus mismatch errors
        repaired_prog = parse_source(repaired_source)
        symbols = SymbolTable(repaired_prog)
        symbols.build_and_validate()
        report = AccessibilityAnalyzer(repaired_prog, symbols).analyze()
    def test_multi_defect_auto_repair(self):
        # A program with multiple simultaneous defects:
        # 1. missing label
        # 2. scrambled tabindex
        # 3. focus trap (missing focus_fallback)
        buggy_source = """
        toggle modalOpen = true;

        Container(id="root", x=0, y=0) {
          Button(id="open-btn", x=0, y=0, label="Open Modal", tabindex=2);
          Group(id="modal", x=50, y=50, show_when=modalOpen) {
            Button(id="modal-close", x=50, y=50, tabindex=1);
          }
        }
        """
        from a11ycc.autorepair import A11yAutoRepair
        repairer = A11yAutoRepair(buggy_source)
        repaired_source, diff_text, repairs = repairer.compute_repair()

        self.assertTrue(len(repairs) >= 2)
        # Verify the repaired code now passes verification!
        prog = parse_source(repaired_source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()
        self.assertFalse(report.has_errors, f"Expected 0 errors after repair, got: {report.to_json()}")


if __name__ == "__main__":
    unittest.main()
