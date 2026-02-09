"""
Master Data Generator Script
Auto-detects all assumptions_*.json files and generates JSON data for each case.
Creates a cases_index.json file listing all available cases.
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime
from typing import Dict, List

# Add project root to path so we can import engelberg package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from engelberg package
from engelberg.analysis import (
    run_base_case_analysis,
    run_sensitivity_analysis,
    run_cash_on_cash_sensitivity_analysis,
    run_monthly_ncf_sensitivity_analysis,
    run_monte_carlo_analysis,
    run_monte_carlo_sensitivity_analysis,
    extract_case_name
)
from engelberg.core import (
    load_assumptions_from_json,
    resolve_path,
    get_project_root
)


def get_case_metadata(assumptions_path: str) -> Dict:
    """
    Load case metadata from assumptions file.
    Returns metadata dict with display_name, description, enabled, etc.
    """
    try:
        assumptions = load_assumptions_from_json(assumptions_path)
        metadata = assumptions.get('_case_metadata', {})
        
        # Extract display name and description from assumptions
        display_name = metadata.get('display_name')
        description = metadata.get('description')
        enabled = metadata.get('enabled', True)
        
        # If not in metadata, try to infer from filename
        if not display_name:
            case_name = extract_case_name(assumptions_path)
            display_name = case_name.replace('_', ' ').title()
        
        if not description:
            financing = assumptions.get('financing', {})
            if financing:
                ltv = financing.get('ltv', 0.75)
                interest = financing.get('interest_rate', 0.013)
                num_owners = financing.get('num_owners', 4)
                description = f"LTV: {ltv*100:.0f}%, Interest: {interest*100:.2f}%, {num_owners} owners"
        
        return {
            'display_name': display_name,
            'description': description,
            'enabled': enabled,
            'assumptions_file': os.path.basename(assumptions_path)
        }
    except Exception as e:
        print(f"  [!] Warning: Could not load metadata from {assumptions_path}: {e}")
        case_name = extract_case_name(assumptions_path)
        return {
            'display_name': case_name.replace('_', ' ').title(),
            'description': f"Case: {case_name}",
            'enabled': True,
            'assumptions_file': os.path.basename(assumptions_path)
        }


def generate_case_data(
    case_name: str,
    assumptions_path: str,
    case_metadata: Dict,
    monte_carlo_simulations: int = 1000,
    include_mc_sensitivity: bool = False,
    mc_sensitivity_simulations: int = 1000
) -> Dict:
    """
    Generate all JSON data for a specific case.
    Runs base case, sensitivity, and Monte Carlo analyses.
    
    Returns:
        Dictionary with status and paths to generated JSON files
    """
    print(f"\n{'='*80}")
    print(f"GENERATING DATA FOR CASE: {case_metadata['display_name']}")
    print(f"{'='*80}")
    print(f"Assumptions file: {assumptions_path}")
    print(f"Case name: {case_name}")
    
    result = {
        'case_name': case_name,
        'display_name': case_metadata['display_name'],
        'assumptions_file': case_metadata['assumptions_file'],
        'base_case_analysis': None,
        'sensitivity': None,
        'sensitivity_coc': None,
        'sensitivity_ncf': None,
        'monte_carlo': None,
        'monte_carlo_sensitivity': None,
        'status': 'success',
        'errors': []
    }
    
    try:
        # Ensure data directory exists
        data_dir = resolve_path("website/data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Run all analyses using unified script
        print(f"\n[*] Running all analyses...")
        try:
            # Run base case
            run_base_case_analysis(assumptions_path, case_name, verbose=False)
            json_path = resolve_path(f"website/data/{case_name}_base_case_analysis.json")
            if os.path.exists(json_path):
                result['base_case_analysis'] = os.path.basename(json_path)
                print(f"  [+] Base case JSON: website/data/{case_name}_base_case_analysis.json")
            
            # Run sensitivity (Equity IRR)
            run_sensitivity_analysis(assumptions_path, case_name, verbose=False)
            json_path = resolve_path(f"website/data/{case_name}_sensitivity.json")
            if os.path.exists(json_path):
                result['sensitivity'] = os.path.basename(json_path)
                print(f"  [+] Sensitivity JSON: website/data/{case_name}_sensitivity.json")
            
            # Run Cash-on-Cash sensitivity
            run_cash_on_cash_sensitivity_analysis(assumptions_path, case_name, verbose=False)
            json_path_coc = resolve_path(f"website/data/{case_name}_sensitivity_coc.json")
            if os.path.exists(json_path_coc):
                result['sensitivity_coc'] = os.path.basename(json_path_coc)
                print(f"  [+] CoC Sensitivity JSON: website/data/{case_name}_sensitivity_coc.json")
            
            # Run Monthly NCF sensitivity
            run_monthly_ncf_sensitivity_analysis(assumptions_path, case_name, verbose=False)
            json_path_ncf = resolve_path(f"website/data/{case_name}_sensitivity_ncf.json")
            if os.path.exists(json_path_ncf):
                result['sensitivity_ncf'] = os.path.basename(json_path_ncf)
                print(f"  [+] NCF Sensitivity JSON: website/data/{case_name}_sensitivity_ncf.json")
            
            # Run Monte Carlo
            run_monte_carlo_analysis(
                assumptions_path,
                case_name,
                n_simulations=monte_carlo_simulations,
                verbose=False
            )
            json_path = resolve_path(f"website/data/{case_name}_monte_carlo.json")
            if os.path.exists(json_path):
                result['monte_carlo'] = os.path.basename(json_path)
                print(f"  [+] Monte Carlo JSON: website/data/{case_name}_monte_carlo.json")
            
            json_path_mc_sens = resolve_path(f"website/data/{case_name}_monte_carlo_sensitivity.json")
            if include_mc_sensitivity:
                run_monte_carlo_sensitivity_analysis(
                    assumptions_path,
                    case_name,
                    num_simulations=mc_sensitivity_simulations,
                    verbose=False
                )
                if os.path.exists(json_path_mc_sens):
                    result['monte_carlo_sensitivity'] = os.path.basename(json_path_mc_sens)
                    print(f"  [+] MC Sensitivity JSON: website/data/{case_name}_monte_carlo_sensitivity.json")
            elif os.path.exists(json_path_mc_sens):
                result['monte_carlo_sensitivity'] = os.path.basename(json_path_mc_sens)
                print("  [=] MC Sensitivity JSON reused (generation skipped)")
            else:
                print("  [~] MC Sensitivity skipped (run scripts/analyze_monte_carlo_sensitivity.py)")
        
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"  [!] {error_msg}")
            result['errors'].append(error_msg)
            result['status'] = 'partial'
    
    except Exception as e:
        error_msg = f"Case generation failed: {str(e)}"
        print(f"  [!] {error_msg}")
        result['errors'].append(error_msg)
        result['status'] = 'failed'
    
    return result


def main():
    """Main function to generate all case data."""
    parser = argparse.ArgumentParser(
        description="Generate dashboard data for all assumptions files."
    )
    parser.add_argument(
        "--monte-carlo-simulations",
        type=int,
        default=1000,
        help="Monte Carlo simulations per case for monte_carlo output (default: 1000)."
    )
    parser.add_argument(
        "--include-mc-sensitivity",
        action="store_true",
        help="Regenerate Monte Carlo sensitivity for each case (slow)."
    )
    parser.add_argument(
        "--mc-sensitivity-simulations",
        type=int,
        default=1000,
        help="Simulations per parameter value for MC sensitivity output (default: 1000)."
    )
    args = parser.parse_args()

    print("="*80)
    print("MASTER DATA GENERATOR")
    print("="*80)
    print("\nThis script will:")
    print("  1. Scan for all assumptions_*.json files")
    print("  2. Generate base case, sensitivity, and Monte Carlo data for each")
    if args.include_mc_sensitivity:
        print("  3. Regenerate Monte Carlo sensitivity data for each case")
    else:
        print("  3. Skip MC sensitivity regeneration (separate script)")
    print("  4. Create cases_index.json with metadata for all cases")
    print()
    
    # Find all assumptions files
    assumptions_files = []
    project_root = get_project_root()
    
    # Check for base assumptions.json in root or assumptions/ directory
    base_paths = [
        os.path.join(project_root, "assumptions.json"),
        os.path.join(project_root, "assumptions", "assumptions.json")
    ]
    for base_path in base_paths:
        if os.path.exists(base_path):
            assumptions_files.append(os.path.relpath(base_path, project_root))
            break
    
    # Find all assumptions_*.json files in root and assumptions/ directory
    root_pattern = os.path.join(project_root, "assumptions_*.json")
    for file in glob.glob(root_pattern):
        rel_path = os.path.relpath(file, project_root)
        if rel_path not in assumptions_files:
            assumptions_files.append(rel_path)
    
    # Also check in assumptions/ subdirectory
    assumptions_pattern = os.path.join(project_root, "assumptions", "assumptions_*.json")
    for file in glob.glob(assumptions_pattern):
        rel_path = os.path.relpath(file, project_root)
        if rel_path not in assumptions_files:
            assumptions_files.append(rel_path)
    
    if not assumptions_files:
        print("[!] No assumptions files found!")
        print("    Expected: assumptions.json or assumptions_*.json")
        return
    
    print(f"[*] Found {len(assumptions_files)} assumptions file(s):")
    for f in assumptions_files:
        print(f"    - {f}")
    print()
    
    # Load metadata for each case
    cases = []
    for assumptions_file in assumptions_files:
        case_name = extract_case_name(assumptions_file)
        metadata = get_case_metadata(assumptions_file)
        
        if not metadata.get('enabled', True):
            print(f"[*] Skipping disabled case: {case_name}")
            continue
        
        cases.append({
            'case_name': case_name,
            'assumptions_file': assumptions_file,
            'metadata': metadata
        })
    
    print(f"\n[*] Processing {len(cases)} case(s)...")
    
    # Generate data for each case
    case_results = []
    for case_info in cases:
        result = generate_case_data(
            case_info['case_name'],
            case_info['assumptions_file'],
            case_info['metadata'],
            monte_carlo_simulations=args.monte_carlo_simulations,
            include_mc_sensitivity=args.include_mc_sensitivity,
            mc_sensitivity_simulations=args.mc_sensitivity_simulations
        )
        case_results.append(result)
    
    # Create cases index
    print(f"\n{'='*80}")
    print("CREATING CASES INDEX")
    print(f"{'='*80}")
    
    cases_index = {
        'cases': [],
        'generated_at': datetime.now().isoformat(),
        'total_cases': len(case_results)
    }
    
    for result in case_results:
        case_entry = {
            'case_name': result['case_name'],
            'display_name': result['display_name'],
            'assumptions_file': result['assumptions_file'],
            'data_files': {
                'base_case_analysis': result.get('base_case_analysis'),
                'sensitivity': result.get('sensitivity'),
                'sensitivity_coc': result.get('sensitivity_coc'),
                'sensitivity_ncf': result.get('sensitivity_ncf'),
                'monte_carlo': result.get('monte_carlo'),
                'monte_carlo_sensitivity': result.get('monte_carlo_sensitivity')
            },
            'status': result['status'],
            'errors': result.get('errors', [])
        }
        cases_index['cases'].append(case_entry)
    
    # Save cases index
    data_dir = resolve_path("website/data")
    os.makedirs(data_dir, exist_ok=True)
    index_path = os.path.join(data_dir, "cases_index.json")
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(cases_index, f, indent=2, ensure_ascii=False)
    
    print(f"[+] Cases index created: website/data/cases_index.json")
    
    # Print summary
    print(f"\n{'='*80}")
    print("GENERATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total cases processed: {len(case_results)}")
    
    successful = sum(1 for r in case_results if r['status'] == 'success')
    partial = sum(1 for r in case_results if r['status'] == 'partial')
    failed = sum(1 for r in case_results if r['status'] == 'failed')
    
    print(f"  - Successful: {successful}")
    print(f"  - Partial: {partial}")
    print(f"  - Failed: {failed}")
    
    if failed > 0 or partial > 0:
        print(f"\nCases with issues:")
        for result in case_results:
            if result['status'] != 'success':
                print(f"  - {result['display_name']}: {result['status']}")
                for error in result.get('errors', []):
                    print(f"      {error}")
    
    print(f"\n[+] Cases index: {index_path}")
    print("="*80)


if __name__ == "__main__":
    main()
