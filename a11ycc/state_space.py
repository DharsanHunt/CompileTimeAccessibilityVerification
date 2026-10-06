"""State space enumerator and transition hypercube generator for Kana-Forge."""

from __future__ import annotations
import itertools
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
from .ast_nodes import ToggleDecl


@dataclass(frozen=True)
class State:
    """Represents a boolean assignment over all declared toggles."""
    assignment: Tuple[Tuple[str, bool], ...]

    @classmethod
    def from_dict(cls, d: Dict[str, bool]) -> "State":
        # Deterministic canonical tuple sorted by toggle name
        sorted_items = tuple(sorted(d.items(), key=lambda x: x[0]))
        return cls(assignment=sorted_items)

    def to_dict(self) -> Dict[str, bool]:
        return dict(self.assignment)

    def get(self, key: str, default: bool = False) -> bool:
        for k, v in self.assignment:
            if k == key:
                return v
        return default

    def diff_key(self, other: "State") -> str:
        """Returns the key that differs between two 1-step adjacent states."""
        d1 = self.to_dict()
        d2 = other.to_dict()
        diffs = [k for k in d1 if d1[k] != d2.get(k)]
        if len(diffs) == 1:
            return diffs[0]
        return ",".join(diffs)

    def __str__(self) -> str:
        items = [f"{k}: {v}" for k, v in self.assignment]
        return "{" + ", ".join(items) + "}"


@dataclass(frozen=True)
class Transition:
    """Directed transition between two states differing by a single toggle."""
    from_state: State
    to_state: State
    toggle_changed: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_state.to_dict(),
            "to": self.to_state.to_dict(),
            "toggle": self.toggle_changed,
        }

    def __str__(self) -> str:
        return f"{self.from_state} --({self.toggle_changed})--> {self.to_state}"


class StateSpace:
    def __init__(self, toggles: List[ToggleDecl]):
        self.toggle_names = sorted([t.name for t in toggles])
        self.default_state = State.from_dict({t.name: t.default for t in toggles})
        self.states: List[State] = []
        self.transitions: List[Transition] = []
        self._build_space()

    def _build_space(self) -> None:
        k = len(self.toggle_names)
        if k == 0:
            s0 = State.from_dict({})
            self.states = [s0]
            self.transitions = []
            return

        # Generate all 2^k boolean combinations deterministically
        for combo in itertools.product([False, True], repeat=k):
            env = {name: val for name, val in zip(self.toggle_names, combo)}
            self.states.append(State.from_dict(env))

        # Generate hypercube transitions (differ in exactly 1 bit)
        for i, s_a in enumerate(self.states):
            dict_a = s_a.to_dict()
            for toggle in self.toggle_names:
                dict_b = dict(dict_a)
                dict_b[toggle] = not dict_a[toggle]
                s_b = State.from_dict(dict_b)
                self.transitions.append(Transition(from_state=s_a, to_state=s_b, toggle_changed=toggle))
