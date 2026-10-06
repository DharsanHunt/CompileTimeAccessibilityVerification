"""Lexical analyzer (Tokenizer) for the Kana-Forge UI DSL."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional
from .ast_nodes import SourcePos


class TokenType(Enum):
    # Keywords
    TOGGLE = auto()
    CONTAINER = auto()
    TEXT = auto()
    BUTTON = auto()
    INPUT = auto()
    GROUP = auto()
    TRUE = auto()
    FALSE = auto()
    PROFILE = auto()  # for @profile directive

    # Identifiers and Literals
    IDENT = auto()
    STRING = auto()
    NUMBER = auto()

    # Symbols & Operators
    EQUALS = auto()      # =
    SEMICOLON = auto()   # ;
    COMMA = auto()       # ,
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    BANG = auto()        # !
    AND = auto()         # &&
    OR = auto()          # ||
    AT = auto()          # @

    # Special
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    pos: SourcePos

    def __str__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, {self.pos})"


class LexerError(Exception):
    """Exception raised when a lexical error is encountered."""
    def __init__(self, message: str, pos: SourcePos):
        super().__init__(f"Lexer error at {pos}: {message}")
        self.message = message
        self.pos = pos


KEYWORDS = {
    "toggle": TokenType.TOGGLE,
    "Container": TokenType.CONTAINER,
    "Text": TokenType.TEXT,
    "Button": TokenType.BUTTON,
    "Input": TokenType.INPUT,
    "Group": TokenType.GROUP,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "profile": TokenType.PROFILE,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<source>"):
        self.source = source
        self.filename = filename
        self.length = len(source)
        self.cursor = 0
        self.line = 1
        self.col = 1

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.cursor + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def _advance(self) -> str:
        ch = self.source[self.cursor]
        self.cursor += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _match(self, expected: str) -> bool:
        if self._peek() == expected:
            self._advance()
            return True
        return False

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.cursor < self.length:
            ch = self._peek()

            # Skip whitespace
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
                continue

            # Skip comments (# or // or /* ... */)
            if ch == '#':
                while self.cursor < self.length and self._peek() != '\n':
                    self._advance()
                continue

            if ch == '/' and self._peek(1) == '/':
                self._advance()
                self._advance()
                while self.cursor < self.length and self._peek() != '\n':
                    self._advance()
                continue

            if ch == '/' and self._peek(1) == '*':
                start_pos = SourcePos(self.line, self.col)
                self._advance()
                self._advance()
                closed = False
                while self.cursor < self.length:
                    if self._peek() == '*' and self._peek(1) == '/':
                        self._advance()
                        self._advance()
                        closed = True
                        break
                    self._advance()
                if not closed:
                    raise LexerError("Unterminated block comment", start_pos)
                continue

            start_line = self.line
            start_col = self.col
            pos = SourcePos(start_line, start_col)

            # Operators and symbols
            if ch == '=':
                self._advance()
                tokens.append(Token(TokenType.EQUALS, "=", pos))
            elif ch == ';':
                self._advance()
                tokens.append(Token(TokenType.SEMICOLON, ";", pos))
            elif ch == ',':
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", pos))
            elif ch == '(':
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", pos))
            elif ch == ')':
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", pos))
            elif ch == '{':
                self._advance()
                tokens.append(Token(TokenType.LBRACE, "{", pos))
            elif ch == '}':
                self._advance()
                tokens.append(Token(TokenType.RBRACE, "}", pos))
            elif ch == '@':
                self._advance()
                tokens.append(Token(TokenType.AT, "@", pos))
            elif ch == '!':
                self._advance()
                tokens.append(Token(TokenType.BANG, "!", pos))
            elif ch == '&':
                self._advance()
                if self._match('&'):
                    tokens.append(Token(TokenType.AND, "&&", pos))
                else:
                    raise LexerError("Unexpected character '&', did you mean '&&'?", pos)
            elif ch == '|':
                self._advance()
                if self._match('|'):
                    tokens.append(Token(TokenType.OR, "||", pos))
                else:
                    raise LexerError("Unexpected character '|', did you mean '||'?", pos)

            # String literals
            elif ch == '"':
                self._advance()
                val_chars = []
                closed = False
                while self.cursor < self.length:
                    curr = self._advance()
                    if curr == '"':
                        closed = True
                        break
                    elif curr == '\\':
                        if self.cursor >= self.length:
                            break
                        esc = self._advance()
                        if esc == 'n':
                            val_chars.append('\n')
                        elif esc == 't':
                            val_chars.append('\t')
                        elif esc == 'r':
                            val_chars.append('\r')
                        elif esc == '"':
                            val_chars.append('"')
                        elif esc == '\\':
                            val_chars.append('\\')
                        else:
                            val_chars.append(esc)
                    else:
                        val_chars.append(curr)
                if not closed:
                    raise LexerError("Unterminated string literal", pos)
                tokens.append(Token(TokenType.STRING, "".join(val_chars), pos))

            # Number literals (including negative numbers like -10 or decimals)
            elif ch.isdigit() or (ch == '-' and self._peek(1) is not None and self._peek(1).isdigit()):
                num_chars = [self._advance()]
                has_dot = False
                while self.cursor < self.length:
                    nxt = self._peek()
                    if nxt and nxt.isdigit():
                        num_chars.append(self._advance())
                    elif nxt == '.' and not has_dot and self._peek(1) and self._peek(1).isdigit():
                        has_dot = True
                        num_chars.append(self._advance())
                    else:
                        break
                tokens.append(Token(TokenType.NUMBER, "".join(num_chars), pos))

            # Identifiers and keywords (including hyphenated identifiers like menu-btn if parsed as ident or attr value)
            elif ch.isalpha() or ch == '_':
                ident_chars = [self._advance()]
                while self.cursor < self.length:
                    nxt = self._peek()
                    if nxt and (nxt.isalnum() or nxt == '_' or nxt == '-'):
                        # Note: we permit '-' in identifiers/names (e.g. menu-btn, sidebar-title)
                        ident_chars.append(self._advance())
                    else:
                        break
                ident_str = "".join(ident_chars)
                token_type = KEYWORDS.get(ident_str, TokenType.IDENT)
                tokens.append(Token(token_type, ident_str, pos))

            else:
                self._advance()
                raise LexerError(f"Unexpected character: {repr(ch)}", pos)

        tokens.append(Token(TokenType.EOF, "", SourcePos(self.line, self.col)))
        return tokens
