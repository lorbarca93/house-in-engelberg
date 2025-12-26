#!/usr/bin/env python3
"""
Monte Carlo Simulation Framework
================================

A comprehensive Monte Carlo simulation framework for financial modeling and risk analysis.

Author: Senior Quantitative Developer
Date: 2025
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.linalg import cholesky
from typing import Dict, List, Tuple, Optional, Callable, Any
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)

class MonteCarloFramework:
    """
    Comprehensive Monte Carlo simulation framework for financial modeling.

    Features:
    - 50,000+ simulations
    - Correlated input variables (Cholesky decomposition)
    - Single-period and time-series outputs
    - Comprehensive risk metrics
    - Multiple visualization types
    """

    def __init__(self, n_simulations: int = 50000):
        """
        Initialize the Monte Carlo framework.

        Parameters:
        -----------
        n_simulations : int
            Number of Monte Carlo simulations to run (default: 50,000)
        """
        self.n_simulations = n_simulations
        self.input_config = {}
        self.correlation_matrix = None
        self.output_functions = {}
        self.results = {}

    def add_input_variable(self, name: str, distribution: str, params: Dict[str, float],
                          description: str = "") -> None:
        """
        Add an input variable to the simulation.

        Parameters:
        -----------
        name : str
            Variable name
        distribution : str
            Distribution type ('normal', 'lognormal', 'uniform', 'triangular', 'beta')
        params : dict
            Distribution parameters
        description : str
            Variable description
        """
        self.input_config[name] = {
            'distribution': distribution,
            'params': params,
            'description': description
        }

    def set_correlation_matrix(self, correlation_matrix: np.ndarray, variable_names: List[str]) -> None:
        """
        Set correlation matrix for input variables.

        Parameters:
        -----------
        correlation_matrix : np.ndarray
            Correlation matrix (must be positive semi-definite)
        variable_names : List[str]
            Variable names in the same order as matrix
        """
        self.correlation_matrix = correlation_matrix
        self.correlated_variables = variable_names

    def add_output_function(self, name: str, func: Callable, output_type: str = 'single',
                           description: str = "") -> None:
        """
        Add an output function to compute simulation results.

        Parameters:
        -----------
        name : str
            Output variable name
        func : callable
            Function that takes input variables dict and returns output
        output_type : str
            'single' for single-period output, 'timeseries' for time-series
        description : str
            Output description
        """
        self.output_functions[name] = {
            'function': func,
            'type': output_type,
            'description': description
        }

    def _generate_uncorrelated_samples(self) -> Dict[str, np.ndarray]:
        """
        Generate uncorrelated samples for all input variables.

        Returns:
        --------
        dict
            Dictionary of input variable samples
        """
        samples = {}

        for name, config in self.input_config.items():
            dist_type = config['distribution']
            params = config['params']

            if dist_type == 'normal':
                samples[name] = np.random.normal(params['mean'], params['std'],
                                               self.n_simulations)
            elif dist_type == 'lognormal':
                # Convert mean/std of lognormal to underlying normal parameters
                mu = np.log(params['mean']**2 / np.sqrt(params['mean']**2 + params['std']**2))
                sigma = np.sqrt(np.log(1 + params['std']**2 / params['mean']**2))
                samples[name] = np.random.lognormal(mu, sigma, self.n_simulations)
            elif dist_type == 'uniform':
                samples[name] = np.random.uniform(params['low'], params['high'],
                                                self.n_simulations)
            elif dist_type == 'triangular':
                samples[name] = np.random.triangular(params['left'], params['mode'],
                                                   params['right'], self.n_simulations)
            elif dist_type == 'beta':
                # Convert mean/std to beta parameters
                mean = params['mean']
                std = params['std']
                var = std**2
                # Use method of moments for beta distribution
                if var < mean * (1 - mean):
                    alpha = mean * (mean * (1 - mean) / var - 1)
                    beta_param = (1 - mean) * (mean * (1 - mean) / var - 1)
                    samples[name] = np.random.beta(alpha, beta_param, self.n_simulations)
                else:
                    # Fallback to uniform if parameters are invalid
                    samples[name] = np.random.uniform(0, 1, self.n_simulations)
            else:
                raise ValueError(f"Unsupported distribution: {dist_type}")

        return samples

    def _apply_correlations(self, uncorrelated_samples: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Apply correlations to input samples using Cholesky decomposition.

        Parameters:
        -----------
        uncorrelated_samples : dict
            Uncorrelated input samples

        Returns:
        --------
        dict
            Correlated input samples
        """
        if self.correlation_matrix is None:
            return uncorrelated_samples

        # Extract samples for correlated variables in matrix order
        correlated_vars = self.correlated_variables
        n_vars = len(correlated_vars)

        # Create matrix of uncorrelated samples
        uncorrelated_matrix = np.column_stack([uncorrelated_samples[var] for var in correlated_vars])

        # Apply Cholesky decomposition
        L = cholesky(self.correlation_matrix, lower=True)

        # Transform to correlated samples
        correlated_matrix = uncorrelated_matrix @ L.T

        # Update samples dictionary
        correlated_samples = uncorrelated_samples.copy()
        for i, var in enumerate(correlated_vars):
            correlated_samples[var] = correlated_matrix[:, i]

        return correlated_samples

    def run_simulation(self) -> Dict[str, Any]:
        """
        Run the Monte Carlo simulation.

        Returns:
        --------
        dict
            Simulation results and metrics
        """
        print(f"Running {self.n_simulations:,} Monte Carlo simulations...")

        # Generate input samples
        uncorrelated_samples = self._generate_uncorrelated_samples()
        input_samples = self._apply_correlations(uncorrelated_samples)

        # Run simulations for each output
        output_results = {}

        for output_name, output_config in self.output_functions.items():
            print(f"Computing {output_name}...")

            func = output_config['function']
            output_type = output_config['type']

            if output_type == 'single':
                # Single-period output
                results = np.array([func({var: samples[i] for var, samples in input_samples.items()})
                                  for i in range(self.n_simulations)])
                output_results[output_name] = results

            elif output_type == 'timeseries':
                # Time-series output (assume function returns array)
                results = np.array([func({var: samples[i] for var, samples in input_samples.items()})
                                  for i in range(self.n_simulations)])
                output_results[output_name] = results
            else:
                raise ValueError(f"Unsupported output type: {output_type}")

        # Calculate risk metrics
        self.results = {
            'input_samples': input_samples,
            'outputs': output_results,
            'metrics': self._calculate_risk_metrics(output_results),
            'n_simulations': self.n_simulations
        }

        print("Simulation completed!")
        return self.results

    def _calculate_risk_metrics(self, outputs: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for all outputs.

        Parameters:
        -----------
        outputs : dict
            Output results from simulations

        Returns:
        --------
        dict
            Risk metrics for each output
        """
        metrics = {}

        for output_name, values in outputs.items():
            if values.ndim == 1:  # Single-period output
                metrics[output_name] = self._calculate_single_metrics(values)
            else:  # Time-series output
                # Calculate metrics for each time period
                time_metrics = []
                for t in range(values.shape[1]):
                    time_metrics.append(self._calculate_single_metrics(values[:, t]))
                metrics[output_name] = time_metrics

        return metrics

    def _calculate_single_metrics(self, values: np.ndarray) -> Dict[str, float]:
        """
        Calculate risk metrics for a single array of values.

        Parameters:
        -----------
        values : np.ndarray
            Array of simulation results

        Returns:
        --------
        dict
            Risk metrics
        """
        # Basic statistics
        mean_val = np.mean(values)
        median_val = np.median(values)
        std_val = np.std(values)

        # Percentiles
        p5 = np.percentile(values, 5)
        p10 = np.percentile(values, 10)
        p25 = np.percentile(values, 25)
        p50 = np.percentile(values, 50)  # Same as median
        p75 = np.percentile(values, 75)
        p90 = np.percentile(values, 90)
        p95 = np.percentile(values, 95)

        # Probabilities
        prob_negative = np.mean(values < 0)

        # Additional metrics
        skewness = stats.skew(values)
        kurtosis = stats.kurtosis(values)

        return {
            'mean': mean_val,
            'median': median_val,
            'std': std_val,
            'p5': p5,
            'p10': p10,
            'p25': p25,
            'p50': p50,
            'p75': p75,
            'p90': p90,
            'p95': p95,
            'prob_negative': prob_negative,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'min': np.min(values),
            'max': np.max(values)
        }

    def create_histogram(self, output_name: str, bins: int = 100,
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        Create histogram with density overlay and key statistics lines.

        Parameters:
        -----------
        output_name : str
            Name of output variable to plot
        bins : int
            Number of histogram bins
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The histogram figure
        """
        if output_name not in self.results['outputs']:
            raise ValueError(f"Output '{output_name}' not found in results")

        values = self.results['outputs'][output_name]
        metrics = self.results['metrics'][output_name]

        fig, ax = plt.subplots(figsize=(12, 8))

        # Histogram with density
        n, bins_edges, patches = ax.hist(values, bins=bins, alpha=0.7, density=True,
                                       color='skyblue', edgecolor='black', linewidth=0.5)

        # Density curve
        density = stats.gaussian_kde(values)
        x_range = np.linspace(values.min(), values.max(), 200)
        ax.plot(x_range, density(x_range), 'r-', linewidth=2, label='Density')

        # Vertical lines for key statistics
        ax.axvline(metrics['mean'], color='red', linestyle='--', linewidth=2,
                  label=f"Mean: {metrics['mean']:.2f}")
        ax.axvline(metrics['median'], color='green', linestyle='--', linewidth=2,
                  label=f"Median: {metrics['median']:.2f}")
        ax.axvline(metrics['p5'], color='orange', linestyle=':', linewidth=2,
                  label=f"P5: {metrics['p5']:.2f}")
        ax.axvline(metrics['p95'], color='purple', linestyle=':', linewidth=2,
                  label=f"P95: {metrics['p95']:.2f}")

        ax.set_xlabel(f'{output_name}', fontsize=12)
        ax.set_ylabel('Density', fontsize=12)
        ax.set_title(f'Distribution of {output_name}\n{self.n_simulations:,} Simulations',
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_cdf_plot(self, output_name: str, save_path: Optional[str] = None) -> plt.Figure:
        """
        Create Cumulative Distribution Function plot.

        Parameters:
        -----------
        output_name : str
            Name of output variable to plot
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The CDF figure
        """
        if output_name not in self.results['outputs']:
            raise ValueError(f"Output '{output_name}' not found in results")

        values = self.results['outputs'][output_name]
        metrics = self.results['metrics'][output_name]

        # Sort values for CDF
        sorted_values = np.sort(values)
        y_vals = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

        fig, ax = plt.subplots(figsize=(12, 8))

        ax.plot(sorted_values, y_vals, 'b-', linewidth=2, label='CDF')

        # Annotate probability of negative values
        prob_neg = metrics['prob_negative']
        if prob_neg > 0.01:  # Only annotate if significant
            zero_idx = np.searchsorted(sorted_values, 0)
            prob_at_zero = zero_idx / len(sorted_values)
            ax.plot([0, 0], [0, prob_at_zero], 'r--', linewidth=2)
            ax.plot([-ax.get_xlim()[1]*0.1, 0], [prob_at_zero, prob_at_zero], 'r--', linewidth=2)
            ax.annotate(f'P(X < 0) = {prob_neg:.1%}',
                       xy=(0, prob_at_zero), xytext=(-50, 10),
                       textcoords='offset points', fontsize=10,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7))

        ax.set_xlabel(f'{output_name}', fontsize=12)
        ax.set_ylabel('Cumulative Probability', fontsize=12)
        ax.set_title(f'Cumulative Distribution Function - {output_name}',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_fan_chart(self, timeseries_output: str, time_points: Optional[List[float]] = None,
                        save_path: Optional[str] = None) -> plt.Figure:
        """
        Create fan chart showing percentile bands over time.

        Parameters:
        -----------
        timeseries_output : str
            Name of time-series output variable
        time_points : list, optional
            Time points for x-axis (if None, uses indices)
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The fan chart figure
        """
        if timeseries_output not in self.results['outputs']:
            raise ValueError(f"Output '{timeseries_output}' not found in results")

        values = self.results['outputs'][timeseries_output]
        if values.ndim != 2:
            raise ValueError(f"'{timeseries_output}' is not a time-series output")

        n_periods = values.shape[1]

        if time_points is None:
            time_points = list(range(n_periods))

        # Calculate percentiles for each time period
        p10 = np.percentile(values, 10, axis=0)
        p25 = np.percentile(values, 25, axis=0)
        p50 = np.percentile(values, 50, axis=0)  # median
        p75 = np.percentile(values, 75, axis=0)
        p90 = np.percentile(values, 90, axis=0)

        fig, ax = plt.subplots(figsize=(14, 8))

        # Fill percentile bands
        ax.fill_between(time_points, p10, p90, alpha=0.2, color='blue',
                       label='10th-90th percentile')
        ax.fill_between(time_points, p25, p75, alpha=0.4, color='blue',
                       label='25th-75th percentile')

        # Median line
        ax.plot(time_points, p50, 'r-', linewidth=3, label='Median')

        ax.set_xlabel('Time Period', fontsize=12)
        ax.set_ylabel(f'{timeseries_output}', fontsize=12)
        ax.set_title(f'Fan Chart - {timeseries_output} Projections\n{self.n_simulations:,} Simulations',
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_spaghetti_plot(self, timeseries_output: str, n_paths: int = 50,
                             time_points: Optional[List[float]] = None,
                             save_path: Optional[str] = None) -> plt.Figure:
        """
        Create spaghetti plot showing individual simulation paths.

        Parameters:
        -----------
        timeseries_output : str
            Name of time-series output variable
        n_paths : int
            Number of random paths to display
        time_points : list, optional
            Time points for x-axis
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The spaghetti plot figure
        """
        if timeseries_output not in self.results['outputs']:
            raise ValueError(f"Output '{timeseries_output}' not found in results")

        values = self.results['outputs'][timeseries_output]
        if values.ndim != 2:
            raise ValueError(f"'{timeseries_output}' is not a time-series output")

        n_periods = values.shape[1]

        if time_points is None:
            time_points = list(range(n_periods))

        # Select random subset of paths
        indices = np.random.choice(self.n_simulations, size=min(n_paths, self.n_simulations),
                                 replace=False)

        fig, ax = plt.subplots(figsize=(14, 8))

        # Plot individual paths
        for idx in indices:
            ax.plot(time_points, values[idx, :], alpha=0.3, linewidth=1, color='blue')

        # Plot median path
        median_path = np.median(values, axis=0)
        ax.plot(time_points, median_path, 'r-', linewidth=3, label='Median Path')

        ax.set_xlabel('Time Period', fontsize=12)
        ax.set_ylabel(f'{timeseries_output}', fontsize=12)
        ax.set_title(f'Spaghetti Plot - {timeseries_output}\n{n_paths} Random Simulation Paths + Median',
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_box_plot_comparison(self, output_name: str, scenarios: Dict[str, np.ndarray],
                                  save_path: Optional[str] = None) -> plt.Figure:
        """
        Create box plot comparing different scenarios or parameter sets.

        Parameters:
        -----------
        output_name : str
            Name of output variable to compare
        scenarios : dict
            Dictionary of scenario names to data arrays
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The box plot figure
        """
        scenario_names = list(scenarios.keys())
        scenario_data = [scenarios[name] for name in scenario_names]

        fig, ax = plt.subplots(figsize=(12, 8))

        bp = ax.boxplot(scenario_data, labels=scenario_names, patch_artist=True)

        # Color the boxes
        colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightcyan']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_ylabel(f'{output_name}', fontsize=12)
        ax.set_title(f'Box Plot Comparison - {output_name}',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_tornado_chart(self, output_name: str, n_variables: int = 10,
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        Create tornado chart showing variable sensitivity using correlation coefficients.

        Parameters:
        -----------
        output_name : str
            Name of output variable
        n_variables : int
            Number of top variables to show
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The tornado chart figure
        """
        if output_name not in self.results['outputs']:
            raise ValueError(f"Output '{output_name}' not found in results")

        output_values = self.results['outputs'][output_name]
        input_samples = self.results['input_samples']

        # Calculate correlation coefficients
        correlations = {}
        for var_name, var_samples in input_samples.items():
            corr = np.corrcoef(var_samples, output_values)[0, 1]
            correlations[var_name] = abs(corr)  # Use absolute value for ranking

        # Sort by absolute correlation
        sorted_vars = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
        top_vars = sorted_vars[:n_variables]

        # Prepare data for tornado chart
        var_names = [var[0] for var in top_vars]
        correlations_abs = [var[1] for var in top_vars]

        fig, ax = plt.subplots(figsize=(12, 8))

        # Create horizontal bar chart
        bars = ax.barh(range(len(var_names)), correlations_abs,
                      color='skyblue', edgecolor='black', alpha=0.7)

        ax.set_yticks(range(len(var_names)))
        ax.set_yticklabels(var_names)
        ax.set_xlabel('Absolute Correlation Coefficient', fontsize=12)
        ax.set_title(f'Tornado Chart - Variable Impact on {output_name}\nRanked by Correlation',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

        # Add correlation values on bars
        for i, (bar, corr) in enumerate(zip(bars, correlations_abs)):
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height()/2,
                   f'{corr:.3f}', ha='left', va='center', fontsize=10)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def create_probability_exceedance(self, output_name: str,
                                     save_path: Optional[str] = None) -> plt.Figure:
        """
        Create probability of exceedance curve P(X ≥ x).

        Parameters:
        -----------
        output_name : str
            Name of output variable
        save_path : str, optional
            Path to save figure

        Returns:
        --------
        matplotlib.figure.Figure
            The exceedance probability figure
        """
        if output_name not in self.results['outputs']:
            raise ValueError(f"Output '{output_name}' not found in results")

        values = self.results['outputs'][output_name]
        metrics = self.results['metrics'][output_name]

        # Sort values in descending order for exceedance
        sorted_values = np.sort(values)[::-1]
        exceedance_probs = np.arange(1, len(sorted_values) + 1) / len(sorted_values)

        fig, ax = plt.subplots(figsize=(12, 8))

        ax.plot(sorted_values, exceedance_probs, 'b-', linewidth=2, label='Exceedance Probability')

        # Highlight P95 and P5 exceedance levels
        p95_value = metrics['p95']
        p5_value = metrics['p5']

        # Find exceedance probabilities
        p95_exceedance = np.mean(values >= p95_value)
        p5_exceedance = np.mean(values >= p5_value)

        ax.axvline(p95_value, color='red', linestyle='--', linewidth=2,
                  label=f'P95 Value: {p95_value:.2f}')
        ax.axhline(p95_exceedance, color='red', linestyle=':', linewidth=2,
                  label=f'P(X ≥ P95) = {p95_exceedance:.1%}')

        ax.axvline(p5_value, color='green', linestyle='--', linewidth=2,
                  label=f'P5 Value: {p5_value:.2f}')
        ax.axhline(p5_exceedance, color='green', linestyle=':', linewidth=2,
                  label=f'P(X ≥ P5) = {p5_exceedance:.1%}')

        ax.set_xlabel(f'{output_name}', fontsize=12)
        ax.set_ylabel('Probability of Exceedance P(X ≥ x)', fontsize=12)
        ax.set_title(f'Probability of Exceedance - {output_name}',
                    fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def generate_all_visualizations(self, output_name: str, timeseries_output: Optional[str] = None,
                                  save_dir: str = "monte_carlo_charts") -> None:
        """
        Generate all required visualizations.

        Parameters:
        -----------
        output_name : str
            Primary output variable for single-period charts
        timeseries_output : str, optional
            Time-series output variable for fan chart and spaghetti plot
        save_dir : str
            Directory to save charts
        """
        import os
        os.makedirs(save_dir, exist_ok=True)

        print("Generating Monte Carlo visualizations...")

        # 1. Histogram
        print("Creating histogram...")
        self.create_histogram(output_name, save_path=f"{save_dir}/histogram.png")

        # 2. CDF
        print("Creating CDF plot...")
        self.create_cdf_plot(output_name, save_path=f"{save_dir}/cdf.png")

        # 3. Fan Chart (if time-series output provided)
        if timeseries_output:
            print("Creating fan chart...")
            self.create_fan_chart(timeseries_output, save_path=f"{save_dir}/fan_chart.png")

            print("Creating spaghetti plot...")
            self.create_spaghetti_plot(timeseries_output, save_path=f"{save_dir}/spaghetti.png")

        # 4. Box Plot (create dummy scenarios for demonstration)
        print("Creating box plot...")
        scenarios = {
            'Base Case': self.results['outputs'][output_name],
            'Optimistic': self.results['outputs'][output_name] * 1.2 + np.random.normal(0, 0.1, self.n_simulations),
            'Pessimistic': self.results['outputs'][output_name] * 0.8 + np.random.normal(0, 0.1, self.n_simulations)
        }
        self.create_box_plot_comparison(output_name, scenarios, save_path=f"{save_dir}/box_plot.png")

        # 5. Tornado Chart
        print("Creating tornado chart...")
        self.create_tornado_chart(output_name, save_path=f"{save_dir}/tornado.png")

        # 6. Probability of Exceedance
        print("Creating exceedance probability plot...")
        self.create_probability_exceedance(output_name, save_path=f"{save_dir}/exceedance.png")

        print(f"All visualizations saved to '{save_dir}' directory")


def create_financial_example() -> MonteCarloFramework:
    """
    Create an example Monte Carlo framework for financial modeling.

    Returns:
    --------
    MonteCarloFramework
        Configured framework for financial analysis
    """
    framework = MonteCarloFramework(n_simulations=50000)

    # Define input variables (with realistic financial parameters)
    framework.add_input_variable(
        'initial_investment',
        'normal',
        {'mean': 1000000, 'std': 100000},
        'Initial capital investment ($)'
    )

    framework.add_input_variable(
        'annual_revenue',
        'normal',
        {'mean': 500000, 'std': 75000},
        'Annual revenue ($)'
    )

    framework.add_input_variable(
        'operating_costs',
        'lognormal',
        {'mean': 300000, 'std': 45000},
        'Annual operating costs ($)'
    )

    framework.add_input_variable(
        'discount_rate',
        'triangular',
        {'left': 0.08, 'mode': 0.12, 'right': 0.18},
        'Annual discount rate'
    )

    framework.add_input_variable(
        'revenue_growth',
        'uniform',
        {'low': 0.02, 'high': 0.08},
        'Annual revenue growth rate'
    )

    # Define correlation matrix for key variables
    correlation_matrix = np.array([
        [1.0,  0.3,  0.2, -0.1,  0.0],  # initial_investment
        [0.3,  1.0,  0.6, -0.2,  0.0],  # annual_revenue
        [0.2,  0.6,  1.0,  0.1,  0.0],  # operating_costs
        [-0.1, -0.2, 0.1,  1.0,  0.3],  # discount_rate
        [0.0,  0.0,  0.0,  0.3,  1.0]   # revenue_growth
    ])

    variable_names = ['initial_investment', 'annual_revenue', 'operating_costs',
                     'discount_rate', 'revenue_growth']
    framework.set_correlation_matrix(correlation_matrix, variable_names)

    # Define output functions
    def calculate_npv(inputs):
        """Calculate NPV for a 5-year project."""
        initial_investment = inputs['initial_investment']
        annual_revenue = inputs['annual_revenue']
        operating_costs = inputs['operating_costs']
        discount_rate = inputs['discount_rate']
        revenue_growth = inputs['revenue_growth']

        # Calculate cash flows for 5 years
        cash_flows = []
        revenue = annual_revenue
        for year in range(1, 6):
            cash_flow = revenue - operating_costs
            pv_cf = cash_flow / (1 + discount_rate) ** year
            cash_flows.append(pv_cf)
            revenue *= (1 + revenue_growth)

        npv = -initial_investment + sum(cash_flows)
        return npv

    def calculate_cash_flows(inputs):
        """Calculate annual cash flows for 5 years."""
        annual_revenue = inputs['annual_revenue']
        operating_costs = inputs['operating_costs']
        revenue_growth = inputs['revenue_growth']

        cash_flows = []
        revenue = annual_revenue
        for year in range(5):
            cash_flow = revenue - operating_costs
            cash_flows.append(cash_flow)
            revenue *= (1 + revenue_growth)

        return np.array(cash_flows)

    framework.add_output_function(
        'NPV',
        calculate_npv,
        output_type='single',
        description='Net Present Value of 5-year project'
    )

    framework.add_output_function(
        'Cash_Flows',
        calculate_cash_flows,
        output_type='timeseries',
        description='Annual cash flows over 5 years'
    )

    return framework


def main():
    """
    Main execution function demonstrating the Monte Carlo framework.
    """
    print("=" * 80)
    print("MONTE CARLO SIMULATION FRAMEWORK")
    print("=" * 80)

    # Create and configure the framework
    framework = create_financial_example()

    print("\nInput Variables:")
    for name, config in framework.input_config.items():
        print(f"  - {name}: {config['distribution']} distribution")

    print(f"\nCorrelated Variables: {len(framework.correlated_variables)}")
    print(f"Output Functions: {len(framework.output_functions)}")

    # Run simulation
    results = framework.run_simulation()

    # Display key metrics for NPV
    npv_metrics = results['metrics']['NPV']
    print("\nNPV Risk Metrics:")
    print(f"  Mean: ${npv_metrics['mean']:,.2f}")
    print(f"  Median: ${npv_metrics['median']:,.2f}")
    print(f"  Std Dev: ${npv_metrics['std']:,.2f}")
    print(f"  P5: ${npv_metrics['p5']:,.2f}")
    print(f"  P95: ${npv_metrics['p95']:,.2f}")
    print(f"  P(X < 0): {npv_metrics['prob_negative']:.1%}")
    print(f"  Skewness: {npv_metrics['skewness']:.2f}")
    print(f"  Kurtosis: {npv_metrics['kurtosis']:.2f}")
    # Generate all visualizations
    framework.generate_all_visualizations(
        output_name='NPV',
        timeseries_output='Cash_Flows',
        save_dir='monte_carlo_charts'
    )

    print("\n" + "=" * 80)
    print("MONTE CARLO ANALYSIS COMPLETED")
    print("All visualizations saved to 'monte_carlo_charts' directory")
    print("=" * 80)


if __name__ == "__main__":
    main()
