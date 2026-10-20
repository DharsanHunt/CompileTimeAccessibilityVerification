"""Unit tests for React JSX/TSX to A11yCC DSL Transpiler."""

import unittest
from a11ycc.transpiler import transpile_jsx_to_dsl
from a11ycc.parser import parse_source
from a11ycc.symbol_table import SymbolTable
from a11ycc.analyzer import AccessibilityAnalyzer


class TestJSXTranspiler(unittest.TestCase):
    def test_transpile_react_modal_component(self):
        jsx = """
        import React, { useState } from 'react';

        export function NotificationDialog() {
            const [isOpen, setIsOpen] = useState(false);

            return (
                <div>
                    <button id="open-btn" onClick={() => setIsOpen(true)}>Open Alerts</button>
                    {isOpen && (
                        <div id="alert-modal" role="dialog" aria-modal="true" data-focus-fallback="open-btn">
                            <button id="close-btn" onClick={() => setIsOpen(false)} data-focus-fallback="open-btn">
                                Dismiss
                            </button>
                            <p id="alert-msg">You have 3 unread messages.</p>
                        </div>
                    )}
                </div>
            );
        }
        """
        dsl = transpile_jsx_to_dsl(jsx)
        self.assertIn("toggle isOpen = false;", dsl)
        self.assertIn('Button(id="open-btn"', dsl)
        self.assertIn('show_when=isOpen', dsl)
        self.assertIn('modal=true', dsl)

        # Ensure the generated DSL compiles cleanly through our parser and analyzer!
        prog = parse_source(dsl)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        analyzer = AccessibilityAnalyzer(prog, symbols)
        report = analyzer.analyze()
        self.assertFalse(report.has_errors, f"Expected clean transpiled DSL, got errors: {report.to_json()}")

    def test_transpile_multiple_conditional_toggles(self):
        jsx = """
        function Dashboard() {
            const [isNavOpen, setIsNavOpen] = useState(true);
            const [isSearchOpen, setIsSearchOpen] = useState(false);

            return (
                <section>
                    <button id="nav-btn">Toggle Nav</button>
                    {isNavOpen && (
                        <aside id="nav-menu">
                            <button id="nav-link-1">Home</button>
                            <button id="nav-link-2">Settings</button>
                        </aside>
                    )}
                    {isSearchOpen && (
                        <div id="search-box">
                            <input id="search-input" label="Search terms" />
                        </div>
                    )}
                </section>
            );
        }
        """
        dsl = transpile_jsx_to_dsl(jsx)
        self.assertIn("toggle isNavOpen = true;", dsl)
        self.assertIn("toggle isSearchOpen = false;", dsl)

        prog = parse_source(dsl)
        symbols = SymbolTable(prog)
        symbols.build_and_validate()
        self.assertEqual(len(symbols.toggles), 2)


if __name__ == "__main__":
    unittest.main()
