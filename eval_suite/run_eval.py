"""Evaluation suite runner for Kana-Forge.

Runs the compiler on all 20 benchmark programs (10 clean, 10 buggy),
diffs actual vs expected diagnostics, and computes precision, recall, and false positive metrics.
"""

from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Set, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from a11ycc.cli import compile_and_verify
from a11ycc.diagnostics import DiagnosticsReport


def evaluate_suite() -> Dict[str, Any]:
    base_dir = Path(__file__).parent
    clean_dir = base_dir / "clean"
    buggy_dir = base_dir / "buggy"
    expected_dir = base_dir / "expected_defects"

    clean_files = sorted(list(clean_dir.glob("clean_*.dsl")))
    buggy_files = sorted(list(buggy_dir.glob("buggy_*.dsl")))

    results = {
        "clean_programs_total": len(clean_files),
        "clean_passed": 0,
        "clean_false_positives": 0,
        "buggy_programs_total": len(buggy_files),
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "program_details": [],
        "total_time_ms": 0.0,
    }

    start_time = time.perf_counter()

    print("=" * 80)
    print(" A11YCC ACCESSIBILITY VERIFICATION EVALUATION SUITE")
    print("=" * 80)
    print(f"\n[1/2] Evaluating {len(clean_files)} Clean Benchmark Programs (Target: 0 False Positives)...")

    # Evaluate clean programs
    for cf in clean_files:
        source = cf.read_text(encoding="utf-8")
        t0 = time.perf_counter()
        report, _ = compile_and_verify(source, filename=str(cf))
        elapsed = (time.perf_counter() - t0) * 1000

        error_diags = [d for d in report.diagnostics if d.severity == "error"]
        passed = (len(error_diags) == 0)

        if passed:
            results["clean_passed"] += 1
            status_str = "✓ PASS (0 errors)"
        else:
            results["clean_false_positives"] += len(error_diags)
            results["false_positives"] += len(error_diags)
            status_str = f"✗ FAIL ({len(error_diags)} false positives)"

        print(f"  - {cf.name:<24} {status_str} [{elapsed:.2f}ms]")
        results["program_details"].append({
            "name": cf.name,
            "type": "clean",
            "passed": passed,
            "actual_errors": [d.to_dict() for d in error_diags],
            "expected_errors": [],
            "elapsed_ms": elapsed,
        })

    print(f"\n[2/2] Evaluating {len(buggy_files)} Buggy Benchmark Programs (Target: >= 90% Recall)...")

    # Evaluate buggy programs
    for bf in buggy_files:
        source = bf.read_text(encoding="utf-8")
        stem = bf.stem
        exp_file = expected_dir / f"{stem}.json"
        expected_defects: List[Dict[str, Any]] = []
        if exp_file.exists():
            expected_defects = json.loads(exp_file.read_text(encoding="utf-8"))

        t0 = time.perf_counter()
        report, _ = compile_and_verify(source, filename=str(bf))
        elapsed = (time.perf_counter() - t0) * 1000

        actual_errors = [d for d in report.diagnostics if d.severity == "error"]

        # Match actual errors against expected defects by (rule, element_id)
        exp_signatures: Set[Tuple[str, str]] = {
            (e["rule"], e["element_id"]) for e in expected_defects
        }
        act_signatures: Set[Tuple[str, str]] = {
            (d.rule, d.element_id or "") for d in actual_errors
        }

        tp = len(exp_signatures & act_signatures)
        fn = len(exp_signatures - act_signatures)
        fp = len(act_signatures - exp_signatures)

        results["true_positives"] += tp
        results["false_negatives"] += fn
        results["false_positives"] += fp

        match_status = "✓ DETECTED" if (fn == 0 and fp == 0) else f"⚠ TP={tp}, FN={fn}, FP={fp}"
        rules_found = ", ".join(sorted(list({d.rule for d in actual_errors})))
        print(f"  - {bf.name:<24} {match_status:<16} Rules: [{rules_found}] [{elapsed:.2f}ms]")

        results["program_details"].append({
            "name": bf.name,
            "type": "buggy",
            "tp": tp,
            "fn": fn,
            "fp": fp,
            "actual_errors": [d.to_dict() for d in actual_errors],
            "expected_errors": expected_defects,
            "elapsed_ms": elapsed,
        })

    total_time = (time.perf_counter() - start_time) * 1000
    results["total_time_ms"] = total_time

    # Calculate metrics
    tp = results["true_positives"]
    fp = results["false_positives"]
    fn = results["false_negatives"]

    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    results["precision"] = precision
    results["recall"] = recall
    results["f1_score"] = f1

    print("\n" + "=" * 80)
    print(" EVALUATION METRICS SUMMARY")
    print("=" * 80)
    print(f"Total Programs Evaluated:    {len(clean_files) + len(buggy_files)}")
    print(f"Clean Programs (0 FP Goal):  {results['clean_passed']}/{results['clean_programs_total']} passed (FP={results['clean_false_positives']})")
    print(f"True Positives (TP):         {tp}")
    print(f"False Positives (FP):        {fp}")
    print(f"False Negatives (FN):        {fn}")
    print(f"Precision:                   {precision * 100:.2f}%")
    print(f"Recall:                      {recall * 100:.2f}% (Requirement: >= 90%)")
    print(f"F1-Score:                    {f1 * 100:.2f}%")
    print(f"Total Execution Time:        {total_time:.2f}ms (Average: {total_time / 20:.2f}ms/program)")
    print("=" * 80)

    return results


if __name__ == "__main__":
    evaluate_suite()
