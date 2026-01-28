"""
MC Sensitivity Analysis Module

This module provides Monte Carlo-based sensitivity analysis for the Engelberg property investment model.
It tests how NPV > 0 probability changes with different parameter values by running Monte Carlo
simulations for each parameter value.

MC Sensitivity combines deterministic parameter variation with probabilistic Monte Carlo simulation
to show risk-adjusted parameter impacts.
"""

import os
import json
from typing import Dict, List, Tuple
from multiprocessing import Pool, cpu_count
from functools import partial

from engelberg.core import (
    create_base_case_config,
    apply_sensitivity,
    export_monte_carlo_sensitivity_to_json,
    resolve_path,
    BaseCaseConfig,
)

from engelberg.monte_carlo import (
    run_monte_carlo_simulation,
    calculate_statistics,
)

from engelberg.mc_sensitivity_ranges import (
    MC_SENSITIVITY_PARAMETER_CONFIG,
)


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def save_json(data: Dict, case_name: str, analysis_type: str) -> str:
    """
    Save analysis results to JSON file.
    
    Args:
        data: Dictionary with analysis results
        case_name: Name of the case (e.g., 'base_case', 'migros')
        analysis_type: Type of analysis (e.g., 'monte_carlo_sensitivity')
    
    Returns:
        Path to saved file (relative to project root)
    """
    data_dir = resolve_path("website/data")
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, f"{case_name}_{analysis_type}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    # Return relative path for compatibility
    return f"website/data/{case_name}_{analysis_type}.json"


def generate_parameter_range(base_value: float, min_factor: float, max_factor: float,
                              num_points: int = 10, clamp_min: float = None, clamp_max: float = None) -> List[float]:
    """
    Generate evenly spaced parameter values for sensitivity analysis.
    
    Args:
        base_value: Base case parameter value
        min_factor: Minimum multiplier (e.g., 0.8 for 80% of base)
        max_factor: Maximum multiplier (e.g., 1.2 for 120% of base)
        num_points: Number of values to generate (default: 10)
        clamp_min: Optional minimum absolute value to clamp to
        clamp_max: Optional maximum absolute value to clamp to
    
    Returns:
        List of parameter values, evenly spaced between min and max
    """
    min_value = base_value * min_factor
    max_value = base_value * max_factor
    
    # Apply clamps if provided
    if clamp_min is not None:
        min_value = max(min_value, clamp_min)
        max_value = max(max_value, clamp_min)
    
    if clamp_max is not None:
        min_value = min(min_value, clamp_max)
        max_value = min(max_value, clamp_max)
    
    # Generate evenly spaced values
    if num_points == 1:
        return [base_value]
    
    # Create linear space between min and max
    values = []
    for i in range(num_points):
        # Linear interpolation: value = min + (max - min) * (i / (num_points - 1))
        factor = i / (num_points - 1) if num_points > 1 else 0
        value = min_value + (max_value - min_value) * factor
        values.append(value)
    
    return values


def run_mc_with_convergence(base_config: BaseCaseConfig, param_key: str, param_val: float,
                           max_simulations: int = 1000, batch_size: int = 100,
                           convergence_threshold: float = 0.005, min_simulations: int = 300) -> float:
    """
    Run Monte Carlo simulation with convergence checking.
    Stops early when NPV probability stabilizes.
    
    Args:
        base_config: Base configuration
        param_key: Parameter key to modify
        param_val: Parameter value to test
        max_simulations: Maximum number of simulations to run
        batch_size: Number of simulations per batch
        convergence_threshold: Probability change threshold for convergence (default: 0.5%)
        min_simulations: Minimum simulations required for statistical validity
    
    Returns:
        NPV > 0 probability
    """
    # Modify config with parameter value
    if param_key == 'amortization_rate':
        modified_config = apply_sensitivity(base_config, amortization_rate=param_val)
    elif param_key == 'interest_rate':
        modified_config = apply_sensitivity(base_config, interest_rate=param_val)
    elif param_key == 'purchase_price':
        modified_config = apply_sensitivity(base_config, purchase_price=param_val)
    elif param_key == 'occupancy':
        modified_config = apply_sensitivity(base_config, occupancy=param_val)
    elif param_key == 'daily_rate':
        modified_config = apply_sensitivity(base_config, daily_rate=param_val)
    else:
        # Unknown parameter - run full simulation
        modified_config = base_config
    
    # Track probability history for convergence checking
    prob_history = []
    total_simulations = 0
    
    # Run in batches until convergence or max reached
    while total_simulations < max_simulations:
        # Calculate batch size (don't exceed max)
        current_batch = min(batch_size, max_simulations - total_simulations)
        
        # Run batch
        # Note: use_parallel=False because this function is called from within parallel workers.
        # Worker processes (daemon processes) cannot spawn child processes, so inner parallelization
        # would cause "daemonic processes are not allowed to have children" errors.
        # The outer parallelization (processing multiple parameter values simultaneously) provides
        # the main speedup, so disabling inner parallelization here is the correct approach.
        df = run_monte_carlo_simulation(
            modified_config,
            num_simulations=current_batch,
            use_lhs=True,
            use_parallel=False  # Disabled to avoid nested multiprocessing issues
        )
        stats = calculate_statistics(df)
        current_prob = stats['npv']['positive_prob']
        prob_history.append(current_prob)
        total_simulations += current_batch
        
        # Check convergence (need at least min_simulations and 3 batches)
        if total_simulations >= min_simulations and len(prob_history) >= 3:
            # Check if last 3 probabilities are stable
            recent_probs = prob_history[-3:]
            max_change = max(recent_probs) - min(recent_probs)
            
            if max_change < convergence_threshold:
                # Converged - return current probability
                return current_prob
    
    # Didn't converge or reached max - return final probability
    return prob_history[-1] if prob_history else 0.0


def run_single_parameter_value_mc(args: Tuple) -> Dict:
    """
    Worker function to run Monte Carlo simulation for a single parameter value.
    Designed to be called in parallel for efficiency.
    
    Args:
        args: Tuple containing (param_key, param_val, base_config, num_simulations, param_name, check_convergence)
    
    Returns:
        Dictionary with parameter value and NPV probability result
    """
    if len(args) == 6:
        param_key, param_val, base_config, num_simulations, param_name, check_convergence = args
    else:
        # Backward compatibility - no convergence checking
        param_key, param_val, base_config, num_simulations, param_name = args
        check_convergence = False
    
    # Use convergence checking if requested
    if check_convergence:
        npv_prob = run_mc_with_convergence(
            base_config, param_key, param_val, 
            max_simulations=num_simulations
        )
    else:
        # Modify config with parameter value
        if param_key == 'amortization_rate':
            modified_config = apply_sensitivity(base_config, amortization_rate=param_val)
        elif param_key == 'interest_rate':
            modified_config = apply_sensitivity(base_config, interest_rate=param_val)
        elif param_key == 'purchase_price':
            modified_config = apply_sensitivity(base_config, purchase_price=param_val)
        elif param_key == 'occupancy':
            modified_config = apply_sensitivity(base_config, occupancy=param_val)
        elif param_key == 'daily_rate':
            modified_config = apply_sensitivity(base_config, daily_rate=param_val)
        else:
            # Unknown parameter - return None to skip
            return None
        
        # Run Monte Carlo simulation with LHS for better accuracy with fewer simulations
        # Note: use_parallel=False because this function is called as a worker by the outer Pool.
        # Worker processes (daemon processes) cannot spawn child processes, so inner parallelization
        # would cause "daemonic processes are not allowed to have children" errors.
        # The outer parallelization (processing multiple parameter values simultaneously) provides
        # the main speedup, so disabling inner parallelization here is the correct approach.
        df = run_monte_carlo_simulation(
            modified_config, 
            num_simulations=num_simulations,
            use_lhs=True,  # Latin Hypercube Sampling provides equivalent accuracy with fewer sims
            use_parallel=False  # Disabled to avoid nested multiprocessing issues
        )
        stats = calculate_statistics(df)
        npv_prob = stats['npv']['positive_prob']
    
    return {
        'param_key': param_key,
        'param_name': param_name,
        'value': param_val,
        'npv_probability': npv_prob
    }


# ═══════════════════════════════════════════════════════════════════════════
# MC SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def run_monte_carlo_sensitivity_analysis(json_path: str, case_name: str,
                                         num_simulations: int = 1000, verbose: bool = True,
                                         check_convergence: bool = True) -> Dict:
    """
    Run MC Sensitivity analysis to show how NPV > 0 probability changes
    with different parameter values.
    
    This analysis combines deterministic parameter variation with probabilistic
    Monte Carlo simulation to show risk-adjusted parameter impacts.
    
    PARAMETERS TESTED (from MC_SENSITIVITY_PARAMETER_CONFIG):
        1. Amortization Rate: Base ± 50% (0% to 2x base, clamped to 0-2%)
        2. Interest Rate: Base ± 50% (0.5% to 2x base, clamped to 0.5%-5%)
        3. Purchase Price: Base ± 20% (0.8x to 1.2x base)
        4. Occupancy Rate: Base ± 20% (0.8x to 1.2x base, clamped to 0-1.0)
        5. Price per Night: Base ± 30% (0.7x to 1.3x base, applied proportionally)
    
    METHODOLOGY:
        - For each parameter, generate 10 evenly spaced values
        - For each value, run Monte Carlo simulation (1000 sims with LHS)
        - Extract NPV > 0 probability from each simulation
        - Show how probability changes across parameter range
    
    PERFORMANCE OPTIMIZATION:
        - Uses Latin Hypercube Sampling (LHS) which achieves similar accuracy
          with 2-3x fewer simulations compared to random sampling
        - Default 1000 simulations with LHS provides equivalent accuracy to
          2000 simulations with random sampling
    
    Args:
        json_path: Path to assumptions JSON file
        case_name: Name of the case
        num_simulations: Maximum number of Monte Carlo simulations per parameter value (default: 1000)
        verbose: Whether to print detailed output
        check_convergence: Whether to use adaptive simulation count with convergence checking (default: True)
                          When enabled, stops early when NPV probability stabilizes, reducing total runtime
    
    Returns:
        Dictionary with sensitivity results including:
        - base_npv_probability: Base case NPV > 0 probability
        - sensitivities: List of parameter sensitivity results
    """
    if verbose:
        print("\n" + "=" * 70)
        print("MC SENSITIVITY ANALYSIS")
        print("=" * 70)
        print(f"  Testing {len(MC_SENSITIVITY_PARAMETER_CONFIG)} parameters with 10 values each")
        print(f"  {num_simulations:,} Monte Carlo simulations per value")
        print(f"  Total simulations: {len(MC_SENSITIVITY_PARAMETER_CONFIG) * 10 * num_simulations:,}")
        print()
    
    # Load base configuration
    base_config = create_base_case_config(json_path)
    
    # Run base case Monte Carlo to get baseline NPV probability
    # Note: use_parallel=True is fine here because this is NOT called from within a worker process.
    # Only the parameter-value combinations run in parallel workers, and those disable inner parallelization.
    if verbose:
        print("[*] Running base case Monte Carlo simulation...")
    df_base = run_monte_carlo_simulation(
        base_config, 
        num_simulations=num_simulations,
        use_lhs=True,  # Latin Hypercube Sampling provides equivalent accuracy with fewer sims
        use_parallel=True  # Safe to use parallel here - not called from a worker process
    )
    stats_base = calculate_statistics(df_base)
    base_npv_prob = stats_base['npv']['positive_prob']
    
    if verbose:
        print(f"  Base Case NPV > 0 Probability: {base_npv_prob * 100:.1f}%")
        print()
    
    sensitivities = []
    
    # Collect all parameter-value combinations for parallel processing
    all_tasks = []
    param_info = {}  # Store parameter info for grouping results
    
    for param_key, param_config in MC_SENSITIVITY_PARAMETER_CONFIG.items():
        # Get base value
        base_value = param_config['get_base_value'](base_config)
        
        # Generate parameter range
        param_values = generate_parameter_range(
            base_value,
            param_config['min_factor'],
            param_config['max_factor'],
            param_config['num_points'],
            param_config.get('clamp_min'),
            param_config.get('clamp_max')
        )
        
        # Store parameter info
        param_info[param_key] = {
            'parameter_name': param_config['parameter_name'],
            'base_value': base_value
        }
        
        # Add all parameter values to task list
        for param_val in param_values:
            all_tasks.append((param_key, param_val, base_config, num_simulations, param_config['parameter_name'], check_convergence))
    
    # Run parameter values in parallel
    if verbose:
        print(f"[*] Running {len(all_tasks)} parameter-value combinations in parallel...")
        num_workers = max(1, cpu_count() - 1)  # Leave one core free
        print(f"    Using {num_workers} parallel workers")
        print()
    
    try:
        # Use parallel processing for parameter-value combinations
        with Pool(processes=max(1, cpu_count() - 1)) as pool:
            completed = 0
            results = []
            
            # Use imap for progress tracking
            chunksize = max(1, len(all_tasks) // (max(1, cpu_count() - 1) * 4))
            for result in pool.imap(run_single_parameter_value_mc, all_tasks, chunksize=chunksize):
                if result is not None:  # Skip None results (unknown parameters)
                    results.append(result)
                completed += 1
                if verbose and completed % max(5, len(all_tasks) // 10) == 0:
                    print(f"  Progress: {completed}/{len(all_tasks)} parameter values ({100 * completed / len(all_tasks):.1f}%)")
    except Exception as e:
        if verbose:
            print(f"  Warning: Parallel processing failed ({e}), falling back to sequential")
        # Fallback to sequential processing
        results = []
        for task in all_tasks:
            result = run_single_parameter_value_mc(task)
            if result is not None:
                results.append(result)
    
    # Group results by parameter
    if verbose:
        print()
    
    for param_key, info in param_info.items():
        if verbose:
            print(f"[*] Processing results for {info['parameter_name']}...")
        
        # Filter results for this parameter
        param_results = [
            {'value': r['value'], 'npv_probability': r['npv_probability']}
            for r in results
            if r['param_key'] == param_key
        ]
        
        # Sort by parameter value to ensure correct order
        param_results.sort(key=lambda x: x['value'])
        
        # Calculate impact
        min_prob = min(r['npv_probability'] for r in param_results)
        max_prob = max(r['npv_probability'] for r in param_results)
        
        sensitivities.append({
            'parameter': info['parameter_name'],
            'base_value': info['base_value'],
            'values': param_results,
            'min_probability': min_prob,
            'max_probability': max_prob,
            'impact': max_prob - min_prob
        })
        
        if verbose:
            print(f"  Range: {min_prob * 100:.1f}% - {max_prob * 100:.1f}% (Impact: {(max_prob - min_prob) * 100:.1f}%)")
            print()
    
    # Sort by impact (highest first)
    sensitivities.sort(key=lambda x: x['impact'], reverse=True)
    
    if verbose:
        print(f"\n{'RESULTS SUMMARY':-^70}")
        print(f"  Base NPV > 0 Probability: {base_npv_prob * 100:.1f}%")
        print(f"\n  Parameter Impact Ranking:")
        for i, sens in enumerate(sensitivities, 1):
            print(f"    {i}. {sens['parameter']:<25} Impact: {(sens['impact'] * 100):.1f}%")
        print()
    
    # Export results
    json_data = export_monte_carlo_sensitivity_to_json(
        case_name, base_npv_prob, sensitivities
    )
    output_path = save_json(json_data, case_name, 'monte_carlo_sensitivity')
    
    if verbose:
        print(f"[+] JSON exported: {output_path}")
    
    return json_data
