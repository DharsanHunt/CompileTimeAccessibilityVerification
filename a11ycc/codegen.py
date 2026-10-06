"""HTML and ARIA code generator for Kana-Forge UI DSL."""

from __future__ import annotations
import html
from typing import Dict, List, Optional
from .ast_nodes import Program, Element, ToggleDecl
from .symbol_table import SymbolTable


class HTMLCodeGenerator:
    def __init__(self, program: Program, symbol_table: SymbolTable):
        self.program = program
        self.symbols = symbol_table
        self.default_env = {t.name: t.default for t in program.toggles}

    def generate(self) -> str:
        body_elements: List[str] = []
        for elem in self.program.elements:
            body_elements.append(self._render_element(elem, indent_level=2))

        toggle_controls_html = self._render_toggle_controls()
        toggle_script = self._render_toggle_script()

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>A11yCC Accessible UI</title>
  <style>
    *, *::before, *::after {{
      box-sizing: border-box;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 24px;
      background-color: #f8fafc;
      color: #0f172a;
    }}
    .kf-stage {{
      position: relative;
      min-height: 600px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .kf-element {{
      position: absolute;
    }}
    .kf-button {{
      padding: 8px 16px;
      background-color: #2563eb;
      color: #ffffff;
      border: none;
      border-radius: 6px;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.15s;
    }}
    .kf-button:hover {{
      background-color: #1d4ed8;
    }}
    .kf-input {{
      padding: 8px 12px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 14px;
    }}
    .kf-text {{
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
    }}
    .kf-group {{
      border: 1px dashed #94a3b8;
      border-radius: 6px;
      padding: 12px;
    }}
    :focus-visible {{
      outline: 3px solid #f59e0b !important;
      outline-offset: 2px !important;
    }}
    .kf-toggle-panel {{
      margin-bottom: 20px;
      padding: 12px 16px;
      background: #f1f5f9;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      display: flex;
      gap: 16px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .kf-toggle-label {{
      font-weight: 600;
      font-size: 13px;
      text-transform: uppercase;
      color: #475569;
    }}
    .kf-toggle-btn {{
      padding: 6px 12px;
      border-radius: 4px;
      border: 1px solid #94a3b8;
      background: #ffffff;
      cursor: pointer;
      font-size: 13px;
    }}
    .kf-toggle-btn[aria-pressed="true"] {{
      background: #0284c7;
      color: white;
      border-color: #0284c7;
    }}
    [hidden] {{
      display: none !important;
    }}
  </style>
</head>
<body>
  {toggle_controls_html}
  <main class="kf-stage" role="main">
{chr(10).join(body_elements)}
  </main>
  {toggle_script}
</body>
</html>"""
        return html_template

    def _render_element(self, elem: Element, indent_level: int = 2) -> str:
        indent = "  " * indent_level
        elem_id = html.escape(str(elem.element_id or ""))
        label = html.escape(str(elem.label or ""))
        x = elem.x
        y = elem.y

        # Style positioning
        style = f"left: {x}px; top: {y}px;"

        # Evaluate visibility in default state
        is_visible = True
        if elem.show_when is not None:
            is_visible = elem.show_when.evaluate(self.default_env)
        hidden_attr = "" if is_visible else " hidden"

        # Tabindex attribute
        tabindex_attr = f' tabindex="{elem.tabindex}"' if elem.tabindex is not None else ""

        # Focus fallback data attribute
        fallback_attr = f' data-focus-fallback="{html.escape(elem.focus_fallback)}"' if elem.focus_fallback else ""

        # Show when expression for client-side JS evaluation
        show_when_attr = f' data-show-when="{html.escape(elem.show_when.to_string())}"' if elem.show_when else ""

        if elem.kind == "Button":
            aria_label = f' aria-label="{label}"' if label else ""
            btn_text = label if label else "Button"
            return (
                f'{indent}<button type="button" id="{elem_id}" class="kf-element kf-button" '
                f'style="{style}"{tabindex_attr}{aria_label}{fallback_attr}{show_when_attr}{hidden_attr}>{btn_text}</button>'
            )

        elif elem.kind == "Input":
            aria_label = f' aria-label="{label}"' if label else ""
            placeholder = f' placeholder="{label}"' if label else ""
            return (
                f'{indent}<input type="text" id="{elem_id}" class="kf-element kf-input" '
                f'style="{style}"{tabindex_attr}{aria_label}{placeholder}{fallback_attr}{show_when_attr}{hidden_attr}>'
            )

        elif elem.kind == "Text":
            text_content = label if label else ""
            return (
                f'{indent}<p id="{elem_id}" class="kf-element kf-text" '
                f'style="{style}"{tabindex_attr}{show_when_attr}{hidden_attr}>{text_content}</p>'
            )

        elif elem.kind in ("Container", "Group"):
            tag = "section" if elem.kind == "Container" else "div"
            role = ' role="region"' if elem.kind == "Container" else ' role="group"'
            aria_label = f' aria-label="{label}"' if label else ""
            cls = "kf-container" if elem.kind == "Container" else "kf-element kf-group"

            children_html = [self._render_element(c, indent_level + 1) for c in elem.children]
            children_str = "\n".join(children_html)

            return (
                f'{indent}<{tag} id="{elem_id}" class="{cls}" style="{style}"{role}{aria_label}{tabindex_attr}{show_when_attr}{hidden_attr}>\n'
                f'{children_str}\n'
                f'{indent}</{tag}>'
            )

        return ""

    def _render_toggle_controls(self) -> str:
        if not self.program.toggles:
            return ""

        buttons = []
        for t in self.program.toggles:
            pressed = "true" if t.default else "false"
            buttons.append(
                f'<button type="button" class="kf-toggle-btn" data-toggle-name="{t.name}" '
                f'aria-pressed="{pressed}" onclick="toggleState(\'{t.name}\')">'
                f'Toggle: {t.name} (<b>{t.name}</b>: <span id="val-{t.name}">{t.default}</span>)</button>'
            )

        return (
            f'<div class="kf-toggle-panel" role="toolbar" aria-label="State Space Simulator">\n'
            f'  <span class="kf-toggle-label">Interactive Toggles:</span>\n'
            f'  {" ".join(buttons)}\n'
            f'</div>'
        )

    def _render_toggle_script(self) -> str:
        if not self.program.toggles:
            return ""

        initial_env_json = {t.name: t.default for t in self.program.toggles}
        return f"""<script>
  const state = {initial_env_json};

  function evaluateExpr(expr, env) {{
    if (!expr) return true;
    // Replace variable names with boolean values
    let jsExpr = expr
      .replace(/&&/g, ' && ')
      .replace(/\\|\\|/g, ' || ')
      .replace(/!/g, ' ! ');
    for (const [k, v] of Object.entries(env)) {{
      const regex = new RegExp('\\\\b' + k + '\\\\b', 'g');
      jsExpr = jsExpr.replace(regex, v ? 'true' : 'false');
    }}
    try {{
      return Boolean(Function('"use strict"; return (' + jsExpr + ')')());
    }} catch (e) {{
      return true;
    }}
  }}

  function toggleState(name) {{
    state[name] = !state[name];
    const valSpan = document.getElementById('val-' + name);
    if (valSpan) valSpan.textContent = state[name];

    const btn = document.querySelector(`[data-toggle-name="${{name}}"]`);
    if (btn) btn.setAttribute('aria-pressed', state[name] ? 'true' : 'false');

    // Update visibility of elements
    const elementsWithCondition = document.querySelectorAll('[data-show-when]');
    elementsWithCondition.forEach(el => {{
      const expr = el.getAttribute('data-show-when');
      const shouldShow = evaluateExpr(expr, state);
      
      if (!shouldShow && !el.hasAttribute('hidden')) {{
        // Element is vanishing: check focus fallback
        if (document.activeElement === el) {{
          const fallbackId = el.getAttribute('data-focus-fallback');
          if (fallbackId) {{
            const fallbackEl = document.getElementById(fallbackId);
            if (fallbackEl && !fallbackEl.hasAttribute('hidden')) {{
              fallbackEl.focus();
            }}
          }}
        }}
        el.setAttribute('hidden', '');
      }} else if (shouldShow && el.hasAttribute('hidden')) {{
        el.removeAttribute('hidden');
      }}
    }});
  }}
</script>"""
