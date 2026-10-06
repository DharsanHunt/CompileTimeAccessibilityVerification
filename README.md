# A11yCC: Compile-Time Accessibility Verification for Declarative UI DSL

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![WCAG 2.1 AA](https://img.shields.io/badge/WCAG-2.1%20AA-orange.svg)](https://www.w3.org/WAI/WCAG21/quickref/)

**A11yCC** is a compiler and compile-time model checker for a declarative UI Domain Specific Language (DSL). Unlike conventional accessibility linters and snapshot test runners (such as `axe-core` and Google Lighthouse) that only inspect a single rendered DOM snapshot, A11yCC performs **exhaustive state-space model checking** ($2^k$ reachable boolean configurations) and **1-toggle transition analysis** across state hypercubes to catch both static and dynamic accessibility defects *before* deployment.

---

## Key Features

1. **State-Space Verification ($2^k$ Reachable States):**
   - Exhaustively computes visibility, visual reading order $(y, x)$, and keyboard focus order across all reachable boolean toggle configurations ($k \le 6$).
   - Flags focus-order mismatches (**WCAG 2.4.3**) when tab sequence diverges from visual reading flow.
2. **Transition-Dependent Defect Detection (Novelty Claim):**
   - Inspects directed edges on the state hypercube $(s_a \to s_b)$ for vanishing interactive elements.
   - Detects potential focus traps / lost focus (**WCAG 2.4.3 / 2.1.2**) when an element disappears without a valid, reachable `focus_fallback`.
3. **Accessible Name / Label Enforcement:**
   - Detects interactive elements (`Button`, `Input`) lacking accessible names (**WCAG 4.1.2**) in any reachable state.
4. **Accessible Code Generation (FR9):**
   - Compiles DSL to semantic, self-contained HTML/ARIA with `:focus-visible` outlines, live toggle simulator toolbar, and automatic focus management scripts.
5. **Constraint-Based Tab Order Auto-Repair (FR10 Stretch):**
   - Automatically repairs scrambled tab orders to match visual layout, emitting a clean unified diff.
6. **Adaptive Accessibility Profiles (FR11 Stretch):**
   - Supports `@profile "screen-reader-first"` and `@profile "switch-access-first"` directives to enforce modality-specific constraints (e.g. text label requirements, spatial jump distance caps).
7. **Zero-Dependency Runtime (NFR4):**
   - Core compiler uses 100% Python standard library.

---

## Architecture & Compiler Pipeline

```
  ┌─────────────────┐
  │  DSL Source     │
  └────────┬────────┘
           │ (Lexer & Tokenizer)
           ▼
  ┌─────────────────┐
  │  Token Stream   │
  └────────┬────────┘
           │ (Recursive Descent Parser)
           ▼
  ┌─────────────────┐
  │   AST Program   │
  └────────┬────────┘
           │ (Symbol Table & Semantic Analysis)
           ▼
  ┌──────────────────────────────────────────────────────────┐
  │ State-Space Engine: Hypercube Generation (2^k States)   │
  ├──────────────────────────────────────────────────────────┤
  │ 1. Static Verification:                                 │
  │    - Visibility Resolution                              │
  │    - Visual Reading Order: sort(y, x)                   │
  │    - Sequential Keyboard Focus Order                    │
  │    - Focus Order Mismatch Check (WCAG 2.4.3)            │
  │    - Missing Label Check (WCAG 4.1.2)                   │
  │ 2. Transition Verification:                             │
  │    - Vanishing Element Set: visible(sa) \ visible(sb)   │
  │    - Reachable Focus Fallback Check (WCAG 2.1.2)        │
  └────────┬─────────────────────────────────────────────────┘
           │
           ├──────────────────────────────┬─────────────────────────────┐
           ▼                              ▼                             ▼
  ┌─────────────────┐           ┌──────────────────┐          ┌──────────────────┐
  │ Diagnostics     │           │ HTML / ARIA Emit │          │ Tab Order Repair │
  │ (Terminal/JSON) │           │ (Default State)  │          │ (Unified Diff)   │
  └─────────────────┘           └──────────────────┘          └──────────────────┘
```

---

## DSL Syntax & Example

```dsl
toggle sidebarOpen = false;

Container(id="root", x=0, y=0) {
  Button(id="menu-btn", x=0, y=0, label="Open menu", tabindex=1);
  Group(id="sidebar", x=0, y=40, show_when=sidebarOpen) {
    Button(id="close-btn", x=0, y=40, label="Close menu",
           tabindex=2, focus_fallback="menu-btn");
    Text(id="sidebar-title", x=0, y=60, label="Navigation");
  }
  Text(id="main-heading", x=100, y=0, label="Welcome");
}
```

---

## CLI Usage

### 1. Verify Accessibility
```bash
# Pretty terminal output
python -m a11ycc check eval_suite/buggy/buggy_08.dsl

# Machine-readable JSON output
python -m a11ycc check eval_suite/buggy/buggy_08.dsl --json
```

### 2. Emit Accessible HTML
```bash
python -m a11ycc emit eval_suite/clean/clean_01.dsl -o build/output.html
```

### 3. Auto-Repair Tab Order
```bash
python -m a11ycc repair eval_suite/buggy/buggy_01.dsl --diff
```

---

## Evaluation Benchmark & Axe-Core Comparison

A11yCC ships with an evaluation suite of **20 benchmark programs** (10 clean, 10 buggy).

```bash
# Run A11yCC Evaluation Suite
python eval_suite/run_eval.py

# Run Axe-Core Baseline Comparison
python eval_suite/run_axe_baseline.py
```

### Results Summary

| Metric | A11yCC | Axe-Core (Static Baseline) |
|---|---|---|
| **Clean Programs (0 False Positives)** | **10 / 10 (100%)** | 10 / 10 (100%) |
| **Static Focus Order Defects** | **4 / 4 (100%)** | 4 / 4 (100%) |
| **Missing Accessible Labels** | **3 / 3 (100%)** | 3 / 3 (100%) |
| **State-Transition Focus Traps** | **3 / 3 (100%)** | **0 / 3 (0.0% - Blindspot)** |
| **Overall Recall** | **100.0%** | **70.0%** |
| **Overall Precision** | **100.0%** | **100.0%** |
| **Verification Speed** | **< 1 ms / program** | ~ 45 ms / program |

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

---

## Project Review 2 Deliverables (75% Milestone)

- **Presentation Slide Deck**: [`A11yCC_Project_Review_2_Presentation.pptx`](A11yCC_Project_Review_2_Presentation.pptx) (13 slides with embedded live studio screenshots, 75% implementation scorecard, empirical benchmark matrices, and future roadmap).
- **Comprehensive Word Report**: [`A11yCC_Project_Review_2_Report.docx`](A11yCC_Project_Review_2_Report.docx) (Full system design, EBNF grammar, formal model checking algorithms, and benchmark evaluation).
- **Interactive Web Studio**: [`a11ycc_lab.html`](a11ycc_lab.html) (Client-side compiler laboratory with dual-pane code editor, live WCAG diagnostic console, and standalone HTML exporter).
- **Presentation Screenshots**: [`presentation_screenshots/`](presentation_screenshots/) (High-resolution cropped figures capturing studio telemetry, defect console, and reactive browser sandbox).
