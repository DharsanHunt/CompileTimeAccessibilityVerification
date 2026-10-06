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
        self.assertFalse(report.has_errors)


if __name__ == "__main__":
    unittest.main()
