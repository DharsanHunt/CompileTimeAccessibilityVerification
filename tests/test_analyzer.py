"""Unit tests for Accessibility Analyzer rules (FR5, FR6, FR7, NFR2)."""

import unittest
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable
from a11ycc.analyzer import AccessibilityAnalyzer


class TestAccessibilityAnalyzer(unittest.TestCase):
    def test_clean_program_passes(self):
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
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()

        self.assertFalse(report.has_errors, f"Expected 0 errors, got: {report.to_json()}")

    def test_missing_label_detection_fr6(self):
        source = """
        Container(id="root", x=0, y=0) {
          Button(id="btn-unlabeled", x=0, y=0);
          Input(id="input-unlabeled", x=0, y=40);
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()

        self.assertTrue(report.has_errors)
        missing_rules = [d for d in report.diagnostics if d.rule == "MissingLabel"]
        self.assertEqual(len(missing_rules), 2)
        flagged_ids = {d.element_id for d in missing_rules}
        self.assertEqual(flagged_ids, {"btn-unlabeled", "input-unlabeled"})
        self.assertEqual(missing_rules[0].wcag, "4.1.2")

    def test_focus_order_mismatch_fr5(self):
        source = """
        Container(id="root", x=0, y=0) {
          Button(id="btn-top", x=0, y=0, label="Top Button", tabindex=2);
          Button(id="btn-bottom", x=0, y=50, label="Bottom Button", tabindex=1);
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()

        self.assertTrue(report.has_errors)
        mismatch_diags = [d for d in report.diagnostics if d.rule == "FocusOrderMismatch"]
        self.assertTrue(len(mismatch_diags) >= 1)
        self.assertEqual(mismatch_diags[0].wcag, "2.4.3")
        self.assertIn("btn-bottom", mismatch_diags[0].message)

    def test_potential_focus_trap_missing_fallback_fr7(self):
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
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()

        self.assertTrue(report.has_errors)
        traps = [d for d in report.diagnostics if d.rule == "PotentialFocusTrap"]
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].element_id, "modal-close")
        self.assertEqual(traps[0].state_path, {"from": {"modalOpen": True}, "to": {"modalOpen": False}})

    def test_potential_focus_trap_invisible_fallback_target_fr7(self):
        source = """
        toggle sidebarOpen = true;

        Container(id="root", x=0, y=0) {
          Button(id="trigger", x=0, y=0, label="Menu");
          Group(id="sidebar", x=0, y=50, show_when=sidebarOpen) {
            Button(id="item1", x=0, y=50, label="Item 1", focus_fallback="item2");
            Button(id="item2", x=0, y=80, label="Item 2", focus_fallback="trigger");
          }
        }
        """
        # When sidebarOpen transitions True -> False, both item1 and item2 disappear.
        # item1's fallback is item2, which is ALSO disappearing!
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()

        self.assertTrue(report.has_errors)
        traps = [d for d in report.diagnostics if d.rule == "PotentialFocusTrap"]
        # item1 has an invisible fallback (item2 vanishes too)
        item1_traps = [t for t in traps if t.element_id == "item1"]
        self.assertEqual(len(item1_traps), 1)
        self.assertIn("not visible in the new state", item1_traps[0].message)

    def test_deterministic_output_nfr2(self):
        source = """
        toggle t1 = true;
        toggle t2 = false;
        Button(id="b2", x=0, y=100, label="B2", tabindex=1);
        Button(id="b1", x=0, y=0, label="B1", tabindex=2);
        Button(id="unlabeled", x=0, y=200);
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()

        report1 = AccessibilityAnalyzer(prog, symbols).analyze().to_json()
        report2 = AccessibilityAnalyzer(prog, symbols).analyze().to_json()
        self.assertEqual(report1, report2)


if __name__ == "__main__":
    unittest.main()
