"""Unit tests for Symbol Table and Semantic Analysis."""

import unittest
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable, SemanticError


class TestSymbolTable(unittest.TestCase):
    def test_duplicate_element_id(self):
        source = """
        Button(id="submit", x=0, y=0, label="Submit");
        Input(id="submit", x=0, y=30, label="Name");
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        with self.assertRaises(SemanticError) as ctx:
            symbols.build_and_validate()
        self.assertIn("Duplicate element ID 'submit'", str(ctx.exception))

    def test_undeclared_toggle_variable(self):
        source = """
        toggle modalOpen = false;
        Button(id="btn", x=0, y=0, label="Save", show_when=undefinedToggle);
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        with self.assertRaises(SemanticError) as ctx:
            symbols.build_and_validate()
        self.assertIn("Undefined toggle variable 'undefinedToggle'", str(ctx.exception))

    def test_invalid_focus_fallback_target(self):
        source = """
        toggle panelOpen = true;
        Button(id="btn", x=0, y=0, label="Close", focus_fallback="non_existent_btn");
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        with self.assertRaises(SemanticError) as ctx:
            symbols.build_and_validate()
        self.assertIn("no element with id 'non_existent_btn' exists", str(ctx.exception))

    def test_nfr1_max_toggle_limit(self):
        source = """
        toggle t1 = false;
        toggle t2 = false;
        toggle t3 = false;
        toggle t4 = false;
        toggle t5 = false;
        toggle t6 = false;
        toggle t7 = false;
        Button(id="btn", x=0, y=0, label="Click");
        """
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        with self.assertRaises(SemanticError) as ctx:
            symbols.build_and_validate()
        self.assertIn("NFR1 Violation", str(ctx.exception))
        self.assertIn("max allowed is 6", str(ctx.exception))

    def test_missing_id_attribute(self):
        source = 'Button(x=0, y=0, label="Click");'
        prog = parse_source(source)
        symbols = SymbolTable(prog)
        with self.assertRaises(SemanticError) as ctx:
            symbols.build_and_validate()
        self.assertIn("missing a non-empty string 'id'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
