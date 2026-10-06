"""Diagnostic models, WCAG criterion tags, and report formatting for A11yCC."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .ast_nodes import SourcePos


RULE_METADATA = {
    "PotentialFocusTrap": {
        "wcag_title": "No Keyboard Trap (2.1.2) & Focus Order (2.4.3) [Level A]",
        "a11y_kind": "State-Transition Focus Management & Vanishing Focus Trap",
        "impacted_users": "Keyboard-only users (focus reset to document body), Screen reader users (loss of interaction context)",
        "default_remediation": "Declare a focus_fallback=\"<target_id>\" pointing to a persistent element that remains visible in the target state.",
    },
    "FocusOrderMismatch": {
        "wcag_title": "Focus Order (2.4.3) [Level A]",
        "a11y_kind": "Sequential Keyboard Navigation & Logical Reading Flow",
        "impacted_users": "Keyboard tab navigators, Switch-access motor users, Cognitive accessibility",
        "default_remediation": "Re-sequence tabindex attributes (1, 2, 3...) to match top-to-bottom, left-to-right visual order (y, x), or run 'python -m a11ycc repair --diff'.",
    },
    "MissingLabel": {
        "wcag_title": "Name, Role, Value (4.1.2) [Level A]",
        "a11y_kind": "Accessible Name & Screen Reader Control Identification",
        "impacted_users": "Blind and low-vision screen reader users (NVDA, JAWS, VoiceOver)",
        "default_remediation": "Add a descriptive label=\"...\" attribute so assistive technology can announce the control's purpose.",
    },
    "MissingTextContent": {
        "wcag_title": "Info and Relationships (1.3.1) [Level A]",
        "a11y_kind": "Text Semantics & Screen Reader Output",
        "impacted_users": "Screen reader users",
        "default_remediation": "Provide non-empty text content or a label attribute for the element.",
    },
    "ExcessiveSwitchJumpDistance": {
        "wcag_title": "Spatial Focus Traversal [Switch Access Profile]",
        "a11y_kind": "Motor Impairment & Physical Scanning Efficiency",
        "impacted_users": "Motor-impaired users utilizing single-switch hardware or scanning grids",
        "default_remediation": "Reduce Euclidean distance between consecutive focus stops to prevent physical scanning disorientation.",
    },
}


@dataclass
class Diagnostic:
    rule: str
    wcag: str
    element_id: Optional[str]
    state_path: Optional[Dict[str, Any]]
    message: str
    severity: str = "error"  # "error" | "warning" | "info"
    pos: Optional[SourcePos] = None
    wcag_title: Optional[str] = None
    a11y_kind: Optional[str] = None
    impacted_users: Optional[str] = None
    remediation: Optional[str] = None

    def __post_init__(self):
        meta = RULE_METADATA.get(self.rule, {})
        if self.wcag_title is None:
            self.wcag_title = meta.get("wcag_title")
        if self.a11y_kind is None:
            self.a11y_kind = meta.get("a11y_kind", "General Accessibility")
        if self.impacted_users is None:
            self.impacted_users = meta.get("impacted_users", "All assistive technology users")
        if self.remediation is None:
            self.remediation = meta.get("default_remediation", "Review and fix the element attributes.")

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "rule": self.rule,
            "wcag": self.wcag,
            "wcag_title": self.wcag_title,
            "a11y_kind": self.a11y_kind,
            "impacted_users": self.impacted_users,
            "element_id": self.element_id,
            "state_path": self.state_path,
            "message": self.message,
            "remediation": self.remediation,
            "severity": self.severity,
        }
        if self.pos is not None:
            d["pos"] = {"line": self.pos.line, "col": self.pos.col}
        return d

    def format_terminal(self, source: Optional[str] = None) -> str:
        loc = f"line {self.pos.line}:{self.pos.col}" if self.pos else "unknown location"
        elem = f" on #{self.element_id}" if self.element_id else ""
        header = f"[{self.severity.upper()}] {self.rule}: {self.a11y_kind}{elem} ({loc})"
        
        res = [
            header,
            f"  WCAG Standard:  WCAG {self.wcag} - {self.wcag_title or 'Accessibility Standard'}",
            f"  Impacted Users: {self.impacted_users}",
            f"  Issue Summary:  {self.message}",
        ]

        if self.state_path:
            if "from" in self.state_path and "to" in self.state_path:
                res.append(f"  State Path:     Transition {self.state_path['from']} -> {self.state_path['to']}")
            elif "state" in self.state_path:
                res.append(f"  Active State:   {self.state_path['state']}")

        if self.remediation:
            res.append(f"  Fix / Remedy:   {self.remediation}")

        if source and self.pos:
            lines = source.splitlines()
            if 1 <= self.pos.line <= len(lines):
                line_text = lines[self.pos.line - 1]
                pointer = " " * max(0, self.pos.col - 1) + "^"
                res.append(f"\n    {line_text}")
                res.append(f"    {pointer}\n")

        return "\n".join(res)


class DiagnosticsReport:
    def __init__(self, diagnostics: Optional[List[Diagnostic]] = None):
        self.diagnostics: List[Diagnostic] = diagnostics or []

    def add(self, diag: Diagnostic) -> None:
        self.diagnostics.append(diag)

    @property
    def has_errors(self) -> bool:
        return any(d.severity == "error" for d in self.diagnostics)

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == "warning")

    def sort_deterministic(self) -> None:
        """Sort diagnostics deterministically for reproducible evaluation (NFR2)."""
        def sort_key(d: Diagnostic):
            line = d.pos.line if d.pos else 0
            col = d.pos.col if d.pos else 0
            elem = d.element_id or ""
            state_str = json.dumps(d.state_path, sort_keys=True) if d.state_path else ""
            return (d.severity, line, col, d.rule, elem, state_str, d.message)

        self.diagnostics.sort(key=sort_key)

    def to_json(self, indent: int = 2) -> str:
        self.sort_deterministic()
        data = [d.to_dict() for d in self.diagnostics]
        return json.dumps(data, indent=indent)

    def to_terminal(self, source: Optional[str] = None) -> str:
        self.sort_deterministic()
        if not self.diagnostics:
            return "✓ Accessibility Verification Passed: 0 violations found."

        parts = [d.format_terminal(source) for d in self.diagnostics]
        summary = f"\nSummary: {self.error_count} error(s), {self.warning_count} warning(s)"
        return "\n\n".join(parts) + "\n" + summary
