"""Unit tests for state space enumeration and transition hypercube generation."""

import unittest
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable
from a11ycc.state_space import StateSpace, State


class TestStateSpace(unittest.TestCase):
    def test_program_with_0_toggles(self):
        """Test Program 1: 0 toggles -> exactly 2^0 = 1 state, 0 transitions."""
        source = 'Button(id="btn", x=0, y=0, label="Submit");'
        prog = parse_source(source)
        space = StateSpace(prog.toggles)

        self.assertEqual(len(space.states), 1)
        self.assertEqual(space.states[0].to_dict(), {})
        self.assertEqual(len(space.transitions), 0)

    def test_program_with_2_toggles(self):
        """Test Program 2: 2 toggles -> exactly 2^2 = 4 states, 8 transitions."""
        source = """
        toggle modalOpen = false;
        toggle darkMode = true;
        Button(id="btn", x=0, y=0, label="Submit");
        """
        prog = parse_source(source)
        space = StateSpace(prog.toggles)

        # Hand-computed states:
        expected_states = [
            {"darkMode": False, "modalOpen": False},
            {"darkMode": False, "modalOpen": True},
            {"darkMode": True, "modalOpen": False},
            {"darkMode": True, "modalOpen": True},
        ]
        actual_states = [s.to_dict() for s in space.states]
        self.assertEqual(len(actual_states), 4)
        for exp in expected_states:
            self.assertIn(exp, actual_states)

        # Hand-computed transitions: 4 states * 2 variables = 8 transitions
        self.assertEqual(len(space.transitions), 8)
        # Default state
        self.assertEqual(space.default_state.to_dict(), {"darkMode": True, "modalOpen": False})

    def test_program_with_3_toggles(self):
        """Test Program 3: 3 toggles -> exactly 2^3 = 8 states, 24 transitions."""
        source = """
        toggle t1 = false;
        toggle t2 = false;
        toggle t3 = true;
        Button(id="btn", x=0, y=0, label="Click");
        """
        prog = parse_source(source)
        space = StateSpace(prog.toggles)

        self.assertEqual(len(space.states), 8)
        # 8 states * 3 variables = 24 directed edges
        self.assertEqual(len(space.transitions), 24)
        self.assertEqual(space.default_state.to_dict(), {"t1": False, "t2": False, "t3": True})

    def test_program_with_6_toggles(self):
        """Test Program 4: 6 toggles (NFR1 bound) -> exactly 2^6 = 64 states, 384 transitions."""
        source = """
        toggle a = false;
        toggle b = false;
        toggle c = false;
        toggle d = false;
        toggle e = false;
        toggle f = false;
        Button(id="btn", x=0, y=0, label="Click");
        """
        prog = parse_source(source)
        space = StateSpace(prog.toggles)

        self.assertEqual(len(space.states), 64)
        self.assertEqual(len(space.transitions), 64 * 6)


if __name__ == "__main__":
    unittest.main()
