"""Unit tests for HTML/ARIA Code Generator (FR9)."""

import unittest
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable
from a11ycc.codegen import HTMLCodeGenerator


class TestHTMLCodeGenerator(unittest.TestCase):
    def test_html_generation_structure(self):
        source = """
        toggle modalOpen = false;

        Container(id="root", x=0, y=0) {
          Button(id="open-btn", x=0, y=0, label="Open Settings", tabindex=1);
          Group(id="modal", x=20, y=20, show_when=modalOpen) {
            Button(id="close-btn", x=20, y=20, label="Close", tabindex=2, focus_fallback="open-btn");
            Input(id="username", x=20, y=60, label="User Name");
          }
        }
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()

        generator = HTMLCodeGenerator(prog, symbols)
        html_output = generator.generate()

        self.assertIn('<!DOCTYPE html>', html_output)
        self.assertIn('<button type="button" id="open-btn"', html_output)
        self.assertIn('aria-label="Open Settings"', html_output)
        self.assertIn('tabindex="1"', html_output)
        self.assertIn('id="modal"', html_output)
        self.assertIn('data-show-when="modalOpen"', html_output)
        self.assertIn('data-focus-fallback="open-btn"', html_output)
        self.assertIn('data-toggle-name="modalOpen"', html_output)
        self.assertIn('<script>', html_output)


if __name__ == "__main__":
    unittest.main()
