"""Command line interface for the Kana-Forge accessibility verification compiler."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Optional

from .parser import parse_source, ParseError
from .symbol_table import SymbolTable, SemanticError
from .analyzer import AccessibilityAnalyzer
from .codegen import HTMLCodeGenerator
from .autorepair import TabOrderAutoRepair
from .profiles import get_profile
from .diagnostics import DiagnosticsReport, Diagnostic


def compile_and_verify(
    source: str,
    filename: str = "<source>",
    profile_override: Optional[str] = None,
) -> tuple[Optional[DiagnosticsReport], Optional[SymbolTable]]:
    report = DiagnosticsReport()
    try:
        program = parse_source(source, filename)
    except ParseError as pe:
        report.add(Diagnostic(
            rule="SyntaxError",
            wcag="",
            element_id=None,
            state_path=None,
            message=pe.message,
            severity="error",
            pos=pe.pos,
        ))
        return report, None

    try:
        symbols = SymbolTable(program)
        symbols.build_and_validate()
    except SemanticError as se:
        report.add(Diagnostic(
            rule="SemanticError",
            wcag="",
            element_id=None,
            state_path=None,
            message=se.message,
            severity="error",
            pos=se.pos,
        ))
        return report, None

    profile = get_profile(profile_override or program.profile)
    analyzer = AccessibilityAnalyzer(program, symbols, profile)
    analysis_report = analyzer.analyze()
    for d in analysis_report.diagnostics:
        report.add(d)

    report.sort_deterministic()
    return report, symbols


def cli_main(args: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="a11ycc",
        description="A11yCC: Compile-Time Accessibility Verification for Declarative UI DSL",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: check
    check_parser = subparsers.add_parser("check", help="Verify accessibility of a DSL file")
    check_parser.add_argument("file", type=str, help="Path to .dsl source file")
    check_parser.add_argument("--json", action="store_true", help="Output diagnostics in JSON format")
    check_parser.add_argument("--profile", type=str, default=None, help="Accessibility profile (standard, screen-reader-first, switch-access-first)")

    # Command: emit
    emit_parser = subparsers.add_parser("emit", help="Compile DSL file to accessible HTML/ARIA")
    emit_parser.add_argument("file", type=str, help="Path to .dsl source file")
    emit_parser.add_argument("-o", "--output", type=str, default=None, help="Output HTML file path")

    # Command: repair
    repair_parser = subparsers.add_parser("repair", help="Auto-repair tab order and generate diff (FR10)")
    repair_parser.add_argument("file", type=str, help="Path to .dsl source file")
    repair_parser.add_argument("--diff", action="store_true", help="Print unified diff to terminal")
    repair_parser.add_argument("-o", "--output", type=str, default=None, help="Write repaired DSL to file")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch interactive A11yCC Lab studio in browser")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")

    parsed_args = parser.parse_args(args)
    if not parsed_args.command:
        parser.print_help()
        return 0

    if parsed_args.command == "serve":
        import http.server
        import socketserver
        import webbrowser
        port = parsed_args.port
        handler = http.server.SimpleHTTPRequestHandler
        print(f"Starting A11yCC Studio at http://localhost:{port}/a11ycc_lab.html ...")
        webbrowser.open(f"http://localhost:{port}/a11ycc_lab.html")
        try:
            with socketserver.TCPServer(("", port), handler) as httpd:
                print("Press Ctrl+C to stop the server.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
        return 0

    file_path = Path(parsed_args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    source = file_path.read_text(encoding="utf-8")

    if parsed_args.command == "check":
        report, _ = compile_and_verify(source, filename=str(file_path), profile_override=parsed_args.profile)
        if parsed_args.json:
            print(report.to_json())
        else:
            print(report.to_terminal(source))
        return 1 if report.has_errors else 0

    elif parsed_args.command == "emit":
        report, symbols = compile_and_verify(source, filename=str(file_path))
        if report.has_errors:
            print("Cannot generate HTML due to verification errors:", file=sys.stderr)
            print(report.to_terminal(source), file=sys.stderr)
            return 1

        generator = HTMLCodeGenerator(symbols.program, symbols)
        html_out = generator.generate()
        if parsed_args.output:
            out_path = Path(parsed_args.output)
            out_path.write_text(html_out, encoding="utf-8")
            print(f"Accessible HTML emitted successfully to: {out_path}")
        else:
            print(html_out)
        return 0

    elif parsed_args.command == "repair":
        try:
            repairer = TabOrderAutoRepair(source)
            repaired_source, diff_text, tab_map = repairer.compute_repair()
            if parsed_args.diff:
                if diff_text:
                    print("--- Tab Order Auto-Repair Diff ---")
                    print(diff_text)
                else:
                    print("No tab order repair needed. All tab indices are already aligned with visual layout.")

            if parsed_args.output:
                out_path = Path(parsed_args.output)
                out_path.write_text(repaired_source, encoding="utf-8")
                print(f"Repaired DSL written to: {out_path}")
            elif not parsed_args.diff:
                print(repaired_source)
            return 0
        except Exception as e:
            print(f"Auto-repair failed: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
