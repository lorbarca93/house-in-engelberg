"""
Master Data Generator Script
Auto-detects all assumptions_*.json files and generates JSON data for each case.
Creates a cases_index.json file listing all available cases.
"""

import os
import json
import glob
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

# Import unified analysis script
import analyze
from core_engine import (
    create_base_case_config,
    load_assumptions_from_json,
    get_projection_defaults
)


def extract_case_name(filename: str) -> str:
    """
    Extract case name from assumptions filename.
    Examples:
        assumptions.json -> base_case
        assumptions_migros.json -> migros
        assumptions_3_owners.json -> 3_owners
    """
    basename = os.path.basename(filename)
    if basename == "assumptions.json":
        return "base_case"
    # Remove "assumptions_" prefix and ".json" suffix
    if basename.startswith("assumptions_") and basename.endswith(".json"):
        return basename[12:-5]  # Remove "assumptions_" (12 chars) and ".json" (5 chars)
    return basename.replace(".json", "")


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


def compute_assumptions_meta(base_path: str = "assumptions.json") -> Dict[str, str]:
    meta = {
        "assumptions_file": base_path if os.path.exists(base_path) else None,
        "assumptions_version": None,
        "assumptions_last_updated": None,
        "assumptions_hash": None,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    if os.path.exists(base_path):
        with open(base_path, "rb") as f:
            meta["assumptions_hash"] = hashlib.sha256(f.read()).hexdigest()
        with open(base_path, "r", encoding="utf-8") as f:
            try:
                parsed = json.load(f)
                meta["assumptions_version"] = parsed.get("_version")
                meta["assumptions_last_updated"] = parsed.get("_last_updated")
            except json.JSONDecodeError:
                pass
    return meta


def generate_case_data(case_name: str, assumptions_path: str, case_metadata: Dict) -> Dict:
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
        'status': 'success',
        'errors': []
    }
    
    try:
        # Ensure data directory exists
        os.makedirs("website/data", exist_ok=True)
        
        # Run all analyses using unified script
        print(f"\n[*] Running all analyses...")
        try:
            # Run base case
            analyze.run_base_case_analysis(assumptions_path, case_name, verbose=False)
            json_path = f"website/data/{case_name}_base_case_analysis.json"
            if os.path.exists(json_path):
                result['base_case_analysis'] = os.path.basename(json_path)
                print(f"  [+] Base case JSON: {json_path}")
            
            # Run sensitivity (Equity IRR)
            analyze.run_sensitivity_analysis(assumptions_path, case_name, verbose=False)
            json_path = f"website/data/{case_name}_sensitivity.json"
            if os.path.exists(json_path):
                result['sensitivity'] = os.path.basename(json_path)
                print(f"  [+] Sensitivity JSON: {json_path}")
            
            # Run Cash-on-Cash sensitivity
            analyze.run_cash_on_cash_sensitivity_analysis(assumptions_path, case_name, verbose=False)
            json_path_coc = f"website/data/{case_name}_sensitivity_coc.json"
            if os.path.exists(json_path_coc):
                result['sensitivity_coc'] = os.path.basename(json_path_coc)
                print(f"  [+] CoC Sensitivity JSON: {json_path_coc}")
            
            # Run Monthly NCF sensitivity
            analyze.run_monthly_ncf_sensitivity_analysis(assumptions_path, case_name, verbose=False)
            json_path_ncf = f"website/data/{case_name}_sensitivity_ncf.json"
            if os.path.exists(json_path_ncf):
                result['sensitivity_ncf'] = os.path.basename(json_path_ncf)
                print(f"  [+] NCF Sensitivity JSON: {json_path_ncf}")
            
            # Run Monte Carlo (10,000 simulations for stable statistics)
            analyze.run_monte_carlo_analysis(assumptions_path, case_name, n_simulations=10000, verbose=False)
            json_path = f"website/data/{case_name}_monte_carlo.json"
            if os.path.exists(json_path):
                result['monte_carlo'] = os.path.basename(json_path)
                print(f"  [+] Monte Carlo JSON: {json_path}")
        
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
    print("="*80)
    print("MASTER DATA GENERATOR")
    print("="*80)
    print("\nThis script will:")
    print("  1. Scan for all assumptions_*.json files")
    print("  2. Generate base case, sensitivity, and Monte Carlo data for each")
    print("  3. Create cases_index.json with metadata for all cases")
    print()
    
    # Find all assumptions files
    assumptions_files = []
    
    # Check for base assumptions.json
    if os.path.exists("assumptions.json"):
        assumptions_files.append("assumptions.json")
    
    # Find all assumptions_*.json files
    for file in glob.glob("assumptions_*.json"):
        if file not in assumptions_files:
            assumptions_files.append(file)
    
    if not assumptions_files:
        print("[!] No assumptions files found!")
        print("    Expected: assumptions.json or assumptions_*.json")
        return
    
    print(f"[*] Found {len(assumptions_files)} assumptions file(s):")
    for f in assumptions_files:
        print(f"    - {f}")
    print()
    
    # Base assumptions meta (single source of truth)
    base_meta = compute_assumptions_meta("assumptions.json")

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
            case_info['metadata']
        )
        case_results.append(result)
    
    # Create cases index
    print(f"\n{'='*80}")
    print("CREATING CASES INDEX")
    print(f"{'='*80}")
    
    cases_index = {
        'cases': [],
        'generated_at': datetime.now().isoformat(),
        'total_cases': len(case_results),
        'assumptions_version': base_meta.get('assumptions_version'),
        'assumptions_hash': base_meta.get('assumptions_hash'),
        'assumptions_last_updated': base_meta.get('assumptions_last_updated')
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
                'monte_carlo': result.get('monte_carlo')
            },
            'status': result['status'],
            'errors': result.get('errors', [])
        }
        cases_index['cases'].append(case_entry)
    
    # Save cases index
    os.makedirs("website/data", exist_ok=True)
    index_path = "website/data/cases_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(cases_index, f, indent=2, ensure_ascii=False)
    
    print(f"[+] Cases index created: {index_path}")
    
    # Write stamp file
    stamp_path = "website/data/.assumptions_hash"
    with open(stamp_path, 'w', encoding='utf-8') as f:
        json.dump(base_meta, f, indent=2, ensure_ascii=False)
    print(f"[+] Assumptions stamp written: {stamp_path}")
    
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

