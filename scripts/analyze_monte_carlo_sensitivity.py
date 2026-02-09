#!/usr/bin/env python
"""
Dedicated Monte Carlo sensitivity runner.

Use this script when you only want to refresh MC sensitivity outputs without
rerunning the full analysis suite.
"""

import argparse
import glob
import os
import sys
from typing import List

# Add project root to path so we can import engelberg package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engelberg.analysis import extract_case_name
from engelberg.core import get_project_root, resolve_path
from engelberg.mc_sensitivity import run_monte_carlo_sensitivity_analysis


def discover_assumptions_files() -> List[str]:
    """Discover base + assumptions_*.json files in supported locations."""
    assumptions_files: List[str] = []
    project_root = get_project_root()

    base_candidates = [
        os.path.join(project_root, "assumptions.json"),
        os.path.join(project_root, "assumptions", "assumptions.json"),
    ]
    for path in base_candidates:
        if os.path.exists(path):
            assumptions_files.append(os.path.relpath(path, project_root))
            break

    patterns = [
        os.path.join(project_root, "assumptions_*.json"),
        os.path.join(project_root, "assumptions", "assumptions_*.json"),
    ]
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            rel_path = os.path.relpath(file_path, project_root)
            if rel_path not in assumptions_files:
                assumptions_files.append(rel_path)

    return assumptions_files


def resolve_assumptions_path(raw_path: str) -> str:
    """Resolve assumptions path using same search order as main analysis script."""
    if os.path.isabs(raw_path):
        return raw_path

    candidates = [
        resolve_path(raw_path),
        resolve_path(f"assumptions/{raw_path}"),
    ]
    if os.path.basename(raw_path) != raw_path:
        candidates.append(resolve_path(f"assumptions/{os.path.basename(raw_path)}"))

    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)

    return os.path.abspath(raw_path)


def run_for_case(assumptions_file: str, simulations: int, quiet: bool) -> bool:
    """Run MC sensitivity for one case and return success status."""
    resolved = resolve_assumptions_path(assumptions_file)
    if not os.path.exists(resolved):
        print(f"[FAIL] Assumptions file not found: {assumptions_file}")
        return False

    case_name = extract_case_name(resolved)
    if not quiet:
        print(f"\n{'=' * 80}")
        print(f"MC SENSITIVITY: {case_name}")
        print(f"{'=' * 80}")
        print(f"Assumptions: {resolved}")
        print(f"Simulations per value: {simulations}")

    try:
        run_monte_carlo_sensitivity_analysis(
            resolved,
            case_name,
            num_simulations=simulations,
            verbose=not quiet,
        )
        output_path = resolve_path(f"website/data/{case_name}_monte_carlo_sensitivity.json")
        if os.path.exists(output_path):
            print(f"[PASS] Generated: website/data/{case_name}_monte_carlo_sensitivity.json")
            return True
        print(f"[FAIL] Expected output missing for case: {case_name}")
        return False
    except Exception as exc:
        print(f"[FAIL] MC sensitivity failed for {case_name}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run only Monte Carlo sensitivity analysis."
    )
    parser.add_argument(
        "assumptions_file",
        nargs="?",
        default="assumptions/assumptions.json",
        help="Assumptions file for single-case run (default: assumptions/assumptions.json).",
    )
    parser.add_argument(
        "--all-cases",
        action="store_true",
        help="Run MC sensitivity for all discovered cases.",
    )
    parser.add_argument(
        "--simulations",
        "-n",
        type=int,
        default=1000,
        help="Simulations per parameter value (default: 1000).",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Reduce console output.",
    )
    args = parser.parse_args()

    if args.all_cases:
        assumption_files = discover_assumptions_files()
        if not assumption_files:
            print("[FAIL] No assumptions files found.")
            sys.exit(1)

        print(f"Running MC sensitivity for {len(assumption_files)} case(s)...")
        successes = 0
        for file_path in assumption_files:
            if run_for_case(file_path, args.simulations, args.quiet):
                successes += 1

        failures = len(assumption_files) - successes
        print(f"\nSummary: {successes} succeeded, {failures} failed")
        sys.exit(0 if failures == 0 else 1)

    success = run_for_case(args.assumptions_file, args.simulations, args.quiet)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
