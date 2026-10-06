"""AST node definitions and expression representation for Kana-Forge."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Dict, List


@dataclass(frozen=True)
class SourcePos:
    line: int
    col: int

    def __str__(self) -> str:
        return f"{self.line}:{self.col}"


class BoolExpr:
    """Base class for boolean visibility expressions in show_when."""

    def evaluate(self, env: Dict[str, bool]) -> bool:
        raise NotImplementedError

    def variables(self) -> set[str]:
        raise NotImplementedError

    def to_string(self) -> str:
        raise NotImplementedError

    def __str__(self) -> str:
        return self.to_string()


@dataclass(frozen=True)
class Var(BoolExpr):
    name: str

    def evaluate(self, env: Dict[str, bool]) -> bool:
        if self.name not in env:
            raise KeyError(f"Undefined toggle variable '{self.name}' in environment")
        return bool(env[self.name])

    def variables(self) -> set[str]:
        return {self.name}

    def to_string(self) -> str:
        return self.name


@dataclass(frozen=True)
class Not(BoolExpr):
    expr: BoolExpr

    def evaluate(self, env: Dict[str, bool]) -> bool:
        return not self.expr.evaluate(env)

    def variables(self) -> set[str]:
        return self.expr.variables()

    def to_string(self) -> str:
        return f"!{self.expr.to_string()}"


@dataclass(frozen=True)
class And(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def evaluate(self, env: Dict[str, bool]) -> bool:
        return self.left.evaluate(env) and self.right.evaluate(env)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def to_string(self) -> str:
        return f"({self.left.to_string()} && {self.right.to_string()})"


@dataclass(frozen=True)
class Or(BoolExpr):
    left: BoolExpr
    right: BoolExpr

    def evaluate(self, env: Dict[str, bool]) -> bool:
        return self.left.evaluate(env) or self.right.evaluate(env)

    def variables(self) -> set[str]:
        return self.left.variables() | self.right.variables()

    def to_string(self) -> str:
        return f"({self.left.to_string()} || {self.right.to_string()})"


@dataclass(frozen=True)
class ConstBool(BoolExpr):
    value: bool

    def evaluate(self, env: Dict[str, bool]) -> bool:
        return self.value

    def variables(self) -> set[str]:
        return set()

    def to_string(self) -> str:
        return "true" if self.value else "false"


@dataclass
class ToggleDecl:
    name: str
    default: bool
    pos: SourcePos


@dataclass
class Element:
    kind: str  # "Container" | "Text" | "Button" | "Input" | "Group"
    attrs: Dict[str, Any]  # id, x, y, tabindex, label, show_when, focus_fallback, etc.
    children: List["Element"] = field(default_factory=list)
    pos: SourcePos = field(default_factory=lambda: SourcePos(1, 1))

    @property
    def element_id(self) -> Optional[str]:
        return self.attrs.get("id")

    @property
    def x(self) -> float:
        return float(self.attrs.get("x", 0))

    @property
    def y(self) -> float:
        return float(self.attrs.get("y", 0))

    @property
    def label(self) -> Optional[str]:
        return self.attrs.get("label")

    @property
    def tabindex(self) -> Optional[int]:
        val = self.attrs.get("tabindex")
        if val is not None:
            return int(val)
        return None

    @property
    def show_when(self) -> Optional[BoolExpr]:
        return self.attrs.get("show_when")

    @property
    def focus_fallback(self) -> Optional[str]:
        return self.attrs.get("focus_fallback")

    @property
    def is_interactive(self) -> bool:
        # Buttons and Inputs are interactive by default, or any element with explicit tabindex >= 0
        if self.kind in ("Button", "Input"):
            return True
        if self.tabindex is not None and self.tabindex >= 0:
            return True
        return False


@dataclass
class Program:
    toggles: List[ToggleDecl]
    elements: List[Element]
    profile: Optional[str] = None
    pos: SourcePos = field(default_factory=lambda: SourcePos(1, 1))
