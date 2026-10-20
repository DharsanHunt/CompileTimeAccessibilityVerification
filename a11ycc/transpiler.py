"""React JSX / TSX to A11yCC DSL Transpiler.

Parses standard React conditional components ({isOpen && <Modal />}, ternary operators)
and translates them directly into A11yCC DSL state hypercubes with zero external dependencies.
"""

from __future__ import annotations
import re
from typing import Dict, List, Tuple, Optional, Any


class JSXTranspiler:
    """Translates React JSX / TSX component trees into formal A11yCC DSL."""

    def __init__(self, jsx_source: str):
        self.raw_source = jsx_source
        self.toggles: Dict[str, bool] = {}
        self.indent_level = 0
        self.element_counter = 0

    def transpile(self) -> str:
        """Main transpilation pipeline: extracts toggles, parses JSX elements, emits DSL."""
        # 1. Clean comments and extract React useState / boolean props
        cleaned = self._clean_source(self.raw_source)
        self._detect_react_state(cleaned)

        # 2. Extract JSX tree
        jsx_body = self._extract_jsx_return(cleaned)

        # 3. Parse JSX tags and conditional expressions into intermediate AST
        root_nodes = self._parse_jsx_body(jsx_body)

        # 4. Generate A11yCC DSL code
        dsl_lines: List[str] = []

        # Emit toggle declarations
        if not self.toggles:
            # If no explicit toggles detected yet, look for conditional identifiers
            cond_vars = re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\s*&&", jsx_body)
            for cv in cond_vars:
                self.toggles[cv] = False

        for name, default_val in sorted(self.toggles.items()):
            dsl_lines.append(f"toggle {name} = {'true' if default_val else 'false'};")

        if self.toggles:
            dsl_lines.append("")

        # Emit Container root
        dsl_lines.append('Container(id="react-root", x=0, y=0) {')
        y_cursor = 0
        for node in root_nodes:
            rendered, y_cursor = self._render_node_dsl(node, indent=1, y_offset=y_cursor)
            dsl_lines.append(rendered)

        dsl_lines.append("}")
        return "\n".join(dsl_lines)

    def _clean_source(self, code: str) -> str:
        # Strip block comments /* ... */
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        # Strip single-line comments // ...
        code = re.sub(r"//.*$", "", code, flags=re.MULTILINE)
        return code

    def _detect_react_state(self, code: str) -> None:
        # Match useState: const [isOpen, setIsOpen] = useState(false)
        state_matches = re.finditer(
            r"const\s+\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*set[a-zA-Z0-9_]+\s*\]\s*=\s*useState\s*\(\s*(true|false)\s*\)",
            code,
        )
        for m in state_matches:
            name = m.group(1)
            default_val = m.group(2) == "true"
            self.toggles[name] = default_val

    def _extract_jsx_return(self, code: str) -> str:
        # Find return (...) or return <...>;
        ret_match = re.search(r"return\s*\(\s*([\s\S]+?)\s*\)\s*;", code)
        if ret_match:
            return ret_match.group(1).strip()

        ret_single = re.search(r"return\s*(<[\s\S]+?>)\s*;", code)
        if ret_single:
            return ret_single.group(1).strip()

        # If raw JSX snippet without function wrapper
        return code.strip()

    def _parse_jsx_body(self, jsx: str) -> List[Dict[str, Any]]:
        """Parses JSX tags and conditional wrappers into an intermediate representation."""
        nodes: List[Dict[str, Any]] = []

        # Tokenize conditional blocks {cond && (<...>)}
        pattern = re.compile(
            r"\{([a-zA-Z_][a-zA-Z0-9_]*)\s*&&\s*(?:\(?\s*)?(<[a-zA-Z0-9]+[^>]*>[\s\S]*?<\/[a-zA-Z0-9]+>|<[a-zA-Z0-9]+[^>]*\/>)(?:\s*\)?)?\}"
        )

        last_end = 0
        for m in pattern.finditer(jsx):
            start, end = m.span()
            before_text = jsx[last_end:start].strip()
            if before_text:
                nodes.extend(self._parse_elements(before_text, cond=None))

            cond_var = m.group(1)
            self.toggles.setdefault(cond_var, False)
            inner_jsx = m.group(2)
            nodes.extend(self._parse_elements(inner_jsx, cond=cond_var))
            last_end = end

        remaining = jsx[last_end:].strip()
        if remaining:
            nodes.extend(self._parse_elements(remaining, cond=None))

        return nodes

    def _parse_elements(self, fragment: str, cond: Optional[str]) -> List[Dict[str, Any]]:
        nodes: List[Dict[str, Any]] = []
        i = 0
        n = len(fragment)

        while i < n:
            start_tag_idx = fragment.find("<", i)
            if start_tag_idx == -1:
                break

            # Skip closing tag if encountered top-level
            if start_tag_idx + 1 < n and fragment[start_tag_idx + 1] == "/":
                close_bracket = fragment.find(">", start_tag_idx)
                if close_bracket == -1:
                    break
                i = close_bracket + 1
                continue

            tag_name_match = re.match(r"<([a-zA-Z0-9]+)", fragment[start_tag_idx:])
            if not tag_name_match:
                i = start_tag_idx + 1
                continue

            tag_name = tag_name_match.group(1).lower()
            tag_name_len = len(tag_name_match.group(0))

            # Scan attributes with brace and quote tracking
            attr_start = start_tag_idx + tag_name_len
            j = attr_start
            brace_depth = 0
            in_quote: Optional[str] = None
            is_self_closing = False
            tag_end = -1

            while j < n:
                ch = fragment[j]
                if in_quote:
                    if ch == in_quote:
                        in_quote = None
                elif ch in ('"', "'", '`'):
                    in_quote = ch
                elif ch == '{':
                    brace_depth += 1
                elif ch == '}':
                    brace_depth = max(0, brace_depth - 1)
                elif ch == '>' and brace_depth == 0 and not in_quote:
                    if j > 0 and fragment[j - 1] == '/':
                        is_self_closing = True
                    tag_end = j
                    break
                j += 1

            if tag_end == -1:
                break

            attr_str = fragment[attr_start:tag_end - (1 if is_self_closing else 0)]
            attrs = self._parse_attrs(attr_str)
            self.element_counter += 1

            elem_id = attrs.get("id") or f"{tag_name}_{self.element_counter}"
            is_modal = attrs.get("role") == "dialog" or attrs.get("aria-modal") == "true" or "modal" in tag_name
            fallback = attrs.get("focus_fallback") or attrs.get("data-focus-fallback")

            node_kind = "Button"
            if tag_name in ("button", "a"):
                node_kind = "Button"
            elif tag_name in ("input", "textarea", "select"):
                node_kind = "Input"
            elif tag_name in ("p", "span", "h1", "h2", "h3", "h4", "label"):
                node_kind = "Text"
            elif tag_name in ("div", "section", "article", "aside", "nav", "modal", "dialog"):
                node_kind = "Group"

            children: List[Dict[str, Any]] = []
            inner_content = ""

            if is_self_closing:
                i = tag_end + 1
            else:
                close_tag_name = f"</{tag_name}>"
                open_tag_prefix = f"<{tag_name}"
                k = tag_end + 1
                depth = 1
                content_start = k
                content_end = k

                while k < n and depth > 0:
                    next_open = fragment.find(open_tag_prefix, k)
                    next_close = fragment.find(close_tag_name, k)

                    if next_close == -1:
                        content_end = n
                        i = n
                        break

                    if next_open != -1 and next_open < next_close:
                        after_char = fragment[next_open + len(open_tag_prefix):next_open + len(open_tag_prefix) + 1]
                        if after_char in (' ', '>', '/', '\t', '\n'):
                            depth += 1
                        k = next_open + len(open_tag_prefix)
                    else:
                        depth -= 1
                        if depth == 0:
                            content_end = next_close
                            i = next_close + len(close_tag_name)
                        else:
                            k = next_close + len(close_tag_name)

                inner_content = fragment[content_start:content_end].strip()
                if node_kind == "Group" and inner_content:
                    children = self._parse_elements(inner_content, cond=None)

            if node_kind == "Group":
                label = attrs.get("aria-label") or attrs.get("label") or ""
            else:
                label = attrs.get("aria-label") or attrs.get("label") or self._extract_text(inner_content)

            nodes.append({
                "kind": node_kind,
                "id": elem_id,
                "label": label or (f"{tag_name.capitalize()} action" if node_kind in ("Button", "Input") else ""),
                "cond": cond,
                "is_modal": is_modal,
                "fallback": fallback,
                "tabindex": attrs.get("tabindex"),
                "children": children,
            })

        return nodes

    def _parse_attrs(self, attr_str: str) -> Dict[str, str]:
        attrs: Dict[str, str] = {}
        # Match attrs key="val", key='val', key={val}
        for m in re.finditer(r'([a-zA-Z0-9_-]+)=(?:"([^"]*)"|\'([^\']*)\'|\{([^}]+)\})', attr_str):
            key = m.group(1)
            val = m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(4))
            attrs[key] = val or ""
        return attrs

    def _extract_text(self, inner: str) -> str:
        # Strip nested tags to find plain direct text
        cleaned = re.sub(r"<[a-zA-Z0-9]+[^>]*?>", "", inner, flags=re.DOTALL)
        cleaned = re.sub(r"</[a-zA-Z0-9]+>", "", cleaned)
        cleaned = re.sub(r"\{[^}]*\}", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _render_node_dsl(self, node: Dict[str, Any], indent: int, y_offset: int) -> Tuple[str, int]:
        spaces = "  " * indent
        kind = node["kind"]
        elem_id = node["id"]
        label = node["label"]
        cond = node["cond"]
        is_modal = node["is_modal"]
        fallback = node["fallback"]
        tabindex = node.get("tabindex")

        attrs_parts = [f'id="{elem_id}"', f"x=0", f"y={y_offset}"]
        if label:
            attrs_parts.append(f'label="{label}"')
        if tabindex is not None:
            attrs_parts.append(f"tabindex={tabindex}")
        if is_modal:
            attrs_parts.append("modal=true")
        if cond:
            attrs_parts.append(f"show_when={cond}")
        if fallback:
            attrs_parts.append(f'focus_fallback="{fallback}"')

        attr_str = ", ".join(attrs_parts)

        if kind == "Group" and node["children"]:
            lines = [f"{spaces}Group({attr_str}) {{"]
            cur_y = y_offset + 30
            for child in node["children"]:
                child_dsl, cur_y = self._render_node_dsl(child, indent + 1, cur_y)
                lines.append(child_dsl)
            lines.append(f"{spaces}}}")
            return "\n".join(lines), cur_y + 40
        elif kind == "Group":
            return f"{spaces}Group({attr_str}) {{}}", y_offset + 40
        else:
            return f"{spaces}{kind}({attr_str});", y_offset + 40


def transpile_jsx_to_dsl(jsx_source: str) -> str:
    """Convenience function to transpile React JSX into A11yCC DSL."""
    transpiler = JSXTranspiler(jsx_source)
    return transpiler.transpile()
