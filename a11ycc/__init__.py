"""A11yCC: Accessibility Compiler Collection - Compile-Time Accessibility Verification for Declarative UI DSL."""

from .ast_nodes import SourcePos, Program, Element, ToggleDecl, BoolExpr
from .lexer import Lexer, Token, TokenType, LexerError
from .parser import Parser, ParseError, parse_source
from .symbol_table import SymbolTable, SemanticError
from .state_space import State, Transition, StateSpace
from .analyzer import AccessibilityAnalyzer
from .diagnostics import Diagnostic, DiagnosticsReport
from .codegen import HTMLCodeGenerator
from .autorepair import TabOrderAutoRepair
from .profiles import AccessibilityProfile, get_profile
from .cli import compile_and_verify, cli_main

__version__ = "1.0.0"
__all__ = [
    "SourcePos",
    "Program",
    "Element",
    "ToggleDecl",
    "BoolExpr",
    "Lexer",
    "Token",
    "TokenType",
    "LexerError",
    "Parser",
    "ParseError",
    "parse_source",
    "SymbolTable",
    "SemanticError",
    "State",
    "Transition",
    "StateSpace",
    "AccessibilityAnalyzer",
    "Diagnostic",
    "DiagnosticsReport",
    "HTMLCodeGenerator",
    "TabOrderAutoRepair",
    "AccessibilityProfile",
    "get_profile",
    "compile_and_verify",
    "cli_main",
]
