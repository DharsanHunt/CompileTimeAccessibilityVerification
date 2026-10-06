"""Symbol table and semantic analysis for Kana-Forge."""

from __future__ import annotations
from typing import Dict, List, Optional, Set
from .ast_nodes import Program, Element, ToggleDecl, SourcePos, BoolExpr


class SemanticError(Exception):
    """Exception raised when a semantic violation is encountered."""
    def __init__(self, message: str, pos: Optional[SourcePos] = None):
        if pos:
            formatted = f"Semantic error at line {pos.line}, column {pos.col}: {message}"
        else:
            formatted = f"Semantic error: {message}"
        super().__init__(formatted)
        self.message = message
        self.pos = pos


class SymbolTable:
    def __init__(self, program: Program):
        self.program = program
        self.toggles: Dict[str, ToggleDecl] = {}
        self.elements: Dict[str, Element] = {}
        self.element_list: List[Element] = []
        self.element_parents: Dict[str, Optional[str]] = {}  # element_id -> parent_element_id

    def build_and_validate(self) -> None:
        # 1. Validate NFR1 toggle limit (N <= 6)
        if len(self.program.toggles) > 6:
            pos = self.program.toggles[6].pos if len(self.program.toggles) > 6 else self.program.pos
            raise SemanticError(
                f"NFR1 Violation: Program declares {len(self.program.toggles)} toggles (max allowed is 6). "
                f"Cap at N <= 6 to keep state-space enumeration bounded.",
                pos,
            )

        # 2. Populate and validate toggles (no duplicates)
        for toggle in self.program.toggles:
            if toggle.name in self.toggles:
                raise SemanticError(
                    f"Duplicate toggle declaration '{toggle.name}'.",
                    toggle.pos,
                )
            self.toggles[toggle.name] = toggle

        # 3. Walk AST to collect elements and check duplicate IDs + required attributes
        for elem in self.program.elements:
            self._collect_elements(elem, parent_id=None)

        # 4. Validate show_when boolean expressions (undeclared toggles)
        for elem in self.element_list:
            if elem.show_when:
                self._validate_bool_expr(elem.show_when, elem.pos)

        # 5. Validate focus_fallback targets exist in element_ids
        for elem in self.element_list:
            if elem.focus_fallback:
                target_id = elem.focus_fallback
                if target_id not in self.elements:
                    raise SemanticError(
                        f"Element '{elem.element_id}' declares focus_fallback='{target_id}', "
                        f"but no element with id '{target_id}' exists in the program.",
                        elem.pos,
                    )
                if target_id == elem.element_id:
                    raise SemanticError(
                        f"Element '{elem.element_id}' declares focus_fallback to itself.",
                        elem.pos,
                    )

    def _collect_elements(self, elem: Element, parent_id: Optional[str]) -> None:
        # Check required attributes: id, x, y
        if "id" not in elem.attrs or not isinstance(elem.attrs["id"], str) or not elem.attrs["id"].strip():
            raise SemanticError(f"Element of kind '{elem.kind}' is missing a non-empty string 'id' attribute.", elem.pos)

        elem_id = elem.attrs["id"]
        if elem_id in self.elements:
            existing = self.elements[elem_id]
            raise SemanticError(
                f"Duplicate element ID '{elem_id}' found. First defined at line {existing.pos.line}, col {existing.pos.col}.",
                elem.pos,
            )

        if "x" not in elem.attrs or not isinstance(elem.attrs["x"], (int, float)):
            raise SemanticError(f"Element '{elem_id}' is missing a numeric 'x' attribute.", elem.pos)

        if "y" not in elem.attrs or not isinstance(elem.attrs["y"], (int, float)):
            raise SemanticError(f"Element '{elem_id}' is missing a numeric 'y' attribute.", elem.pos)

        if "tabindex" in elem.attrs:
            val = elem.attrs["tabindex"]
            if not isinstance(val, int) or isinstance(val, bool):
                raise SemanticError(f"Element '{elem_id}' has invalid tabindex '{val}'. Must be an integer.", elem.pos)

        self.elements[elem_id] = elem
        self.element_list.append(elem)
        self.element_parents[elem_id] = parent_id

        for child in elem.children:
            self._collect_elements(child, parent_id=elem_id)

    def _validate_bool_expr(self, expr: BoolExpr, pos: SourcePos) -> None:
        for var_name in expr.variables():
            if var_name not in self.toggles:
                raise SemanticError(
                    f"Undefined toggle variable '{var_name}' in show_when expression.",
                    pos,
                )

    def get_ancestors(self, elem_id: str) -> List[Element]:
        """Return list of ancestor elements from immediate parent up to root."""
        ancestors = []
        curr = self.element_parents.get(elem_id)
        while curr is not None:
            ancestor_elem = self.elements[curr]
            ancestors.append(ancestor_elem)
            curr = self.element_parents.get(curr)
        return ancestors
