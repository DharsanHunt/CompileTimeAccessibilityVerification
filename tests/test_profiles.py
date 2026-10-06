"""Unit tests for Accessibility Profiles (FR11 stretch)."""

import unittest
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable
from a11ycc.analyzer import AccessibilityAnalyzer
from a11ycc.profiles import get_profile


class TestProfiles(unittest.TestCase):
    def test_screen_reader_first_profile(self):
        # In standard profile, Text without label is allowed.
        # In screen-reader-first profile, Text without label is flagged with a warning.
        source = """
        @profile "screen-reader-first";

        Container(id="root", x=0, y=0) {
          Button(id="btn", x=0, y=0, label="Click me");
          Text(id="unlabeled-text", x=0, y=50);
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        report = AccessibilityAnalyzer(prog, symbols).analyze()

        warnings = [d for d in report.diagnostics if d.rule == "MissingTextContent"]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].element_id, "unlabeled-text")

    def test_switch_access_first_profile_jump_distance(self):
        source = """
        @profile "switch-access-first";

        Container(id="root", x=0, y=0) {
          Button(id="btn1", x=0, y=0, label="Top Left");
          Button(id="btn2", x=800, y=800, label="Far Bottom Right");
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        report = AccessibilityAnalyzer(prog, symbols).analyze()

        jump_warnings = [d for d in report.diagnostics if d.rule == "ExcessiveSwitchJumpDistance"]
        self.assertEqual(len(jump_warnings), 1)
        self.assertEqual(jump_warnings[0].element_id, "btn2")


if __name__ == "__main__":
    unittest.main()
