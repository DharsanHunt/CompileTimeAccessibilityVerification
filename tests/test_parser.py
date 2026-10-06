"""Unit tests for Kana-Forge Parser."""

import unittest
from a11ycc.parser import parse_source, ParseError
from a11ycc.ast_nodes import Var, Not, And, Or, ConstBool


class TestParser(unittest.TestCase):
    def test_parse_example_program(self):
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
        self.assertEqual(len(prog.toggles), 1)
        self.assertEqual(prog.toggles[0].name, "sidebarOpen")
        self.assertEqual(prog.toggles[0].default, False)

        self.assertEqual(len(prog.elements), 1)
        root = prog.elements[0]
        self.assertEqual(root.kind, "Container")
        self.assertEqual(root.element_id, "root")
        self.assertEqual(len(root.children), 3)

        menu_btn = root.children[0]
        self.assertEqual(menu_btn.kind, "Button")
        self.assertEqual(menu_btn.element_id, "menu-btn")
        self.assertEqual(menu_btn.tabindex, 1)

        sidebar = root.children[1]
        self.assertEqual(sidebar.kind, "Group")
        self.assertIsInstance(sidebar.show_when, Var)
        self.assertEqual(sidebar.show_when.name, "sidebarOpen")

        close_btn = sidebar.children[0]
        self.assertEqual(close_btn.focus_fallback, "menu-btn")

    def test_parse_boolean_expression_precedence(self):
        source = """
        toggle a = true;
        toggle b = false;
        toggle c = true;

        Button(id="btn", x=0, y=0, label="Click", show_when=a || !b && c);
        """
        prog = parse_source(source)
        btn = prog.elements[0]
        # Precedence: !b && c is evaluated before ||
        # Result: Or(Var(a), And(Not(Var(b)), Var(c)))
        expr = btn.show_when
        self.assertIsInstance(expr, Or)
        self.assertIsInstance(expr.left, Var)
        self.assertEqual(expr.left.name, "a")
        self.assertIsInstance(expr.right, And)
        self.assertIsInstance(expr.right.left, Not)
        self.assertIsInstance(expr.right.right, Var)

    def test_parse_syntax_error_reporting(self):
        source = "toggle missingEquals true;"
        with self.assertRaises(ParseError) as ctx:
            parse_source(source)
        self.assertIn("line 1, column 22", str(ctx.exception))
        self.assertIn("Expected '='", str(ctx.exception))

    def test_parse_missing_semicolon(self):
        source = 'Button(id="btn", x=0, y=0, label="Test")'
        with self.assertRaises(ParseError) as ctx:
            parse_source(source)
        self.assertIn("Expected ';'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
