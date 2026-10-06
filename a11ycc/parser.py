"""Recursive descent parser for the Kana-Forge UI DSL."""

from __future__ import annotations
from typing import List, Optional, Any, Dict
from .ast_nodes import (
    SourcePos,
    BoolExpr,
    Var,
    Not,
    And,
    Or,
    ConstBool,
    ToggleDecl,
    Element,
    Program,
)
from .lexer import Token, TokenType, Lexer, LexerError


class ParseError(Exception):
    """Exception raised when a syntax error is encountered during parsing."""
    def __init__(self, message: str, pos: SourcePos, source: Optional[str] = None):
        formatted = f"Syntax error at line {pos.line}, column {pos.col}: {message}"
        if source:
            lines = source.splitlines()
            if 1 <= pos.line <= len(lines):
                line_str = lines[pos.line - 1]
                pointer = " " * (max(0, pos.col - 1)) + "^"
                formatted += f"\n\n  {line_str}\n  {pointer}"
        super().__init__(formatted)
        self.message = message
        self.pos = pos


class Parser:
    def __init__(self, tokens: List[Token], source: Optional[str] = None):
        self.tokens = tokens
        self.source = source
        self.cursor = 0

    def _peek(self, offset: int = 0) -> Token:
        idx = self.cursor + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def _match(self, *expected_types: TokenType) -> bool:
        if self._peek().type in expected_types:
            self._advance()
            return True
        return False

    def _check(self, *expected_types: TokenType) -> bool:
        return self._peek().type in expected_types

    def _advance(self) -> Token:
        tok = self._peek()
        if self.cursor < len(self.tokens) - 1:
            self.cursor += 1
        return tok

    def _expect(self, expected_type: TokenType, err_msg: Optional[str] = None) -> Token:
        tok = self._peek()
        if tok.type != expected_type:
            msg = err_msg or f"Expected '{expected_type.name}', but found '{tok.type.name}' ({repr(tok.value)})"
            raise ParseError(msg, tok.pos, self.source)
        return self._advance()

    def parse(self) -> Program:
        toggles: List[ToggleDecl] = []
        elements: List[Element] = []
        profile: Optional[str] = None
        prog_pos = self._peek().pos

        # Parse directives or toggle declarations
        while not self._check(TokenType.EOF):
            # Check for @profile directive
            if self._check(TokenType.AT):
                self._advance()
                self._expect(TokenType.PROFILE, "Expected 'profile' keyword after '@'")
                # Can be followed by STRING or IDENT
                val_tok = self._peek()
                if val_tok.type in (TokenType.STRING, TokenType.IDENT):
                    profile = self._advance().value
                else:
                    raise ParseError("Expected profile name as string or identifier after '@profile'", val_tok.pos, self.source)
                self._expect(TokenType.SEMICOLON, "Expected ';' after profile directive")
                continue

            # Check for toggle declaration
            if self._check(TokenType.TOGGLE):
                toggles.append(self._parse_toggle_decl())
                continue

            # Break to parse elements
            break

        # Parse top-level elements
        while not self._check(TokenType.EOF):
            elements.append(self._parse_element())

        return Program(toggles=toggles, elements=elements, profile=profile, pos=prog_pos)

    def _parse_toggle_decl(self) -> ToggleDecl:
        toggle_tok = self._expect(TokenType.TOGGLE)
        ident_tok = self._expect(TokenType.IDENT, "Expected toggle identifier name")
        self._expect(TokenType.EQUALS, "Expected '=' in toggle declaration")

        val_tok = self._peek()
        if val_tok.type == TokenType.TRUE:
            self._advance()
            default_val = True
        elif val_tok.type == TokenType.FALSE:
            self._advance()
            default_val = False
        else:
            raise ParseError(f"Expected 'true' or 'false' for toggle default value, found '{val_tok.value}'", val_tok.pos, self.source)

        self._expect(TokenType.SEMICOLON, "Expected ';' after toggle declaration")
        return ToggleDecl(name=ident_tok.value, default=default_val, pos=toggle_tok.pos)

    def _parse_element(self) -> Element:
        tok = self._peek()
        kind_map = {
            TokenType.CONTAINER: "Container",
            TokenType.TEXT: "Text",
            TokenType.BUTTON: "Button",
            TokenType.INPUT: "Input",
            TokenType.GROUP: "Group",
        }

        if tok.type not in kind_map:
            raise ParseError(
                f"Expected element ('Container', 'Text', 'Button', 'Input', 'Group'), but found '{tok.value}'",
                tok.pos,
                self.source,
            )

        self._advance()
        kind = kind_map[tok.type]
        elem_pos = tok.pos

        # Parse attribute list in parentheses
        self._expect(TokenType.LPAREN, f"Expected '(' after '{kind}'")
        attrs = self._parse_attr_list()
        self._expect(TokenType.RPAREN, f"Expected ')' after attribute list for '{kind}'")

        # Container and Group have body in braces: { element* }
        # Text, Button, Input end with semicolon: ;
        children: List[Element] = []
        if kind in ("Container", "Group"):
            self._expect(TokenType.LBRACE, f"Expected '{{' for '{kind}' body")
            while not self._check(TokenType.RBRACE, TokenType.EOF):
                children.append(self._parse_element())
            self._expect(TokenType.RBRACE, f"Expected '}}' to close '{kind}' body")
        else:
            self._expect(TokenType.SEMICOLON, f"Expected ';' after '{kind}' element")

        return Element(kind=kind, attrs=attrs, children=children, pos=elem_pos)

    def _parse_attr_list(self) -> Dict[str, Any]:
        attrs: Dict[str, Any] = {}
        if self._check(TokenType.RPAREN):
            return attrs

        while True:
            # Parse key = value
            key_tok = self._expect(TokenType.IDENT, "Expected attribute name")
            self._expect(TokenType.EQUALS, f"Expected '=' after attribute '{key_tok.value}'")

            attr_name = key_tok.value
            if attr_name == "show_when":
                attr_val = self._parse_bool_expr()
            else:
                attr_val = self._parse_attr_value(attr_name)

            attrs[attr_name] = attr_val

            if self._match(TokenType.COMMA):
                continue
            else:
                break

        return attrs

    def _parse_attr_value(self, attr_name: str) -> Any:
        tok = self._peek()
        if tok.type == TokenType.STRING:
            self._advance()
            return tok.value
        elif tok.type == TokenType.NUMBER:
            self._advance()
            try:
                if "." in tok.value:
                    return float(tok.value)
                return int(tok.value)
            except ValueError:
                return float(tok.value)
        elif tok.type == TokenType.TRUE:
            self._advance()
            return True
        elif tok.type == TokenType.FALSE:
            self._advance()
            return False
        elif tok.type == TokenType.IDENT:
            self._advance()
            return tok.value
        else:
            raise ParseError(
                f"Unexpected value '{tok.value}' for attribute '{attr_name}'",
                tok.pos,
                self.source,
            )

    def _parse_bool_expr(self) -> BoolExpr:
        return self._parse_or_expr()

    def _parse_or_expr(self) -> BoolExpr:
        left = self._parse_and_expr()
        while self._match(TokenType.OR):
            right = self._parse_and_expr()
            left = Or(left, right)
        return left

    def _parse_and_expr(self) -> BoolExpr:
        left = self._parse_unary_expr()
        while self._match(TokenType.AND):
            right = self._parse_unary_expr()
            left = And(left, right)
        return left

    def _parse_unary_expr(self) -> BoolExpr:
        if self._match(TokenType.BANG):
            inner = self._parse_unary_expr()
            return Not(inner)
        return self._parse_primary_bool()

    def _parse_primary_bool(self) -> BoolExpr:
        tok = self._peek()
        if tok.type == TokenType.TRUE:
            self._advance()
            return ConstBool(True)
        elif tok.type == TokenType.FALSE:
            self._advance()
            return ConstBool(False)
        elif tok.type == TokenType.IDENT:
            self._advance()
            return Var(tok.value)
        elif self._match(TokenType.LPAREN):
            expr = self._parse_bool_expr()
            self._expect(TokenType.RPAREN, "Expected ')' after boolean expression")
            return expr
        else:
            raise ParseError(f"Expected boolean expression, but found '{tok.value}'", tok.pos, self.source)


def parse_source(source: str, filename: str = "<source>") -> Program:
    """Convenience helper to tokenize and parse DSL source text into a Program AST."""
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source)
    return parser.parse()
