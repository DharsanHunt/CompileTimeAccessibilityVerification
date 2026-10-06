"""Accessibility profiles (FR11 stretch) for specialized user modalities."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Set


@dataclass(frozen=True)
class AccessibilityProfile:
    name: str
    description: str
    require_text_labels: bool = False
    max_switch_jump_distance: Optional[float] = None
    strict_focus_order: bool = True


PROFILES = {
    "standard": AccessibilityProfile(
        name="standard",
        description="Standard WCAG 2.1 AA compile-time verification profile",
        require_text_labels=False,
        max_switch_jump_distance=None,
        strict_focus_order=True,
    ),
    "screen-reader-first": AccessibilityProfile(
        name="screen-reader-first",
        description="Screen-reader-optimized profile enforcing accessible names on all Text and Container elements",
        require_text_labels=True,
        max_switch_jump_distance=None,
        strict_focus_order=True,
    ),
    "switch-access-first": AccessibilityProfile(
        name="switch-access-first",
        description="Switch-access profile penalizing large spatial distance jumps between consecutive tab stops",
        require_text_labels=False,
        max_switch_jump_distance=500.0,
        strict_focus_order=True,
    ),
}


def get_profile(name: Optional[str]) -> AccessibilityProfile:
    if not name:
        return PROFILES["standard"]
    normalized = name.strip().lower()
    if normalized in PROFILES:
        return PROFILES[normalized]
    raise ValueError(f"Unknown accessibility profile '{name}'. Available: {list(PROFILES.keys())}")
