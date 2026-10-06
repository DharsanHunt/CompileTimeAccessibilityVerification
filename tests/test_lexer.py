"""Unit tests for Kana-Forge Lexer."""

import unittest
from a11ycc.lexer import Lexer, TokenType, LexerError
from a11ycc.ast_nodes import SourcePos


class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        source = 'toggle sidebarOpen = false;\nButton(id="btn-1", x=10, y=20, label="Click");'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        expected_types = [
            TokenType.TOGGLE,
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.FALSE,
            TokenType.SEMICOLON,
            TokenType.BUTTON,
            TokenType.LPAREN,
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.STRING,
            TokenType.COMMA,
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.NUMBER,
            TokenType.COMMA,
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.NUMBER,
            TokenType.COMMA,
            TokenType.IDENT,
            TokenType.EQUALS,
            TokenType.STRING,
            TokenType.RPAREN,
            TokenType.SEMICOLON,
            TokenType.EOF,
        ]

        actual_types = [t.type for t in tokens]
        self.assertEqual(actual_types, expected_types)
        self.assertEqual(tokens[1].value, "sidebarOpen")
        self.assertEqual(tokens[9].value, "btn-1")

    def test_line_and_col_tracking(self):
        source = 'toggle a = true;\ntoggle b = false;'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # toggle at line 1, col 1
        self.assertEqual(tokens[0].pos, SourcePos(1, 1))
        # toggle at line 2, col 1
        self.assertEqual(tokens[5].pos, SourcePos(2, 1))

    def test_boolean_expression_tokens(self):
        source = 'show_when = (a && !b) || c'
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        types = [t.type for t in tokens]
        self.assertIn(TokenType.LPAREN, types)
        self.assertIn(TokenType.AND, types)
        self.assertIn(TokenType.BANG, types)
        self.assertIn(TokenType.OR, types)
        self.assertIn(TokenType.RPAREN, types)

    def test_comments_skipping(self):
        source = """
        # This is a comment
        toggle dark = true; // Another comment
        /* Block comment
           multiline */
        Button(id="ok", x=0, y=0, label="OK");
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        token_types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(token_types[0], TokenType.TOGGLE)
        self.assertEqual(token_types[5], TokenType.BUTTON)

    def test_unterminated_string_error(self):
        source = 'Button(id="unclosed);'
        lexer = Lexer(source)
        with self.assertRaises(LexerError) as ctx:
            lexer.tokenize()
        self.assertIn("Unterminated string literal", str(ctx.exception))

    def test_invalid_character_error(self):
        source = 'toggle a = true $;'
        lexer = Lexer(source)
        with self.assertRaises(LexerError) as ctx:
            lexer.tokenize()
        self.assertIn("Unexpected character: '$'", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
