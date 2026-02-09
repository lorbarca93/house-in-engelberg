"""
Integration tests for Monte Carlo simulation workflows
"""

import pytest
import numpy as np
from engelberg.core import create_base_case_config
from engelberg.monte_carlo import (
    run_monte_carlo_simulation,
    calculate_statistics,
    DistributionConfig,
    sample_correlated_variables
)
from engelberg.analysis import run_monte_carlo_analysis
from tests.conftest import sample_assumptions_path


class TestMonteCarloSimulation:
    """Tests for run_monte_carlo_simulation()."""
    
    def test_simulation_count_default(self, sample_assumptions_path):
        """Test default simulation count (100)."""
        config = create_base_case_config(sample_assumptions_path)
        df = run_monte_carlo_simulation(config, num_simulations=100)
        
        assert df is not None
        assert len(df) == 100
        assert 'npv' in df.columns
        assert 'irr_with_sale' in df.columns
    
    def test_simulation_count_custom(self, sample_assumptions_path):
        """Test custom simulation count."""
        config = create_base_case_config(sample_assumptions_path)
        df = run_monte_carlo_simulation(config, num_simulations=500)
        
        assert df is not None
        assert len(df) == 500
    
    def test_distribution_sampling_uniform(self):
        """Test uniform distribution sampling."""
        dist = DistributionConfig(
            dist_type='uniform',
            params={'min': 0.0, 'max': 1.0}
        )
        
        samples = dist.sample(size=1000)
        
        assert len(samples) == 1000
        assert all(0.0 <= s <= 1.0 for s in samples)
        # Mean should be approximately 0.5
        assert np.mean(samples) == pytest.approx(0.5, abs=0.1)
    
    def test_distribution_sampling_normal(self):
        """Test normal distribution sampling."""
        dist = DistributionConfig(
            dist_type='normal',
            params={'mean': 100.0, 'std': 10.0}
        )
        
        samples = dist.sample(size=1000)
        
        assert len(samples) == 1000
        # Mean should be approximately 100
        assert np.mean(samples) == pytest.approx(100.0, abs=5.0)
        # Std dev should be approximately 10
        assert np.std(samples) == pytest.approx(10.0, abs=2.0)
    
    def test_distribution_sampling_triangular(self):
        """Test triangular distribution sampling."""
        dist = DistributionConfig(
            dist_type='triangular',
            params={'min': 0.0, 'mode': 0.5, 'max': 1.0}
        )
        
        samples = dist.sample(size=1000)
        
        assert len(samples) == 1000
        assert all(0.0 <= s <= 1.0 for s in samples)
    
    def test_distribution_sampling_beta(self):
        """Test beta distribution sampling."""
        dist = DistributionConfig(
            dist_type='beta',
            params={'alpha': 2.0, 'beta': 2.0, 'min': 0.0, 'max': 1.0}
        )
        
        samples = dist.sample(size=1000)
        
        assert len(samples) == 1000
        assert all(0.0 <= s <= 1.0 for s in samples)
    
    def test_distribution_sampling_lognormal(self):
        """Test lognormal distribution sampling."""
        dist = DistributionConfig(
            dist_type='lognormal',
            params={'mean': 0.0, 'std': 1.0}
        )
        
        samples = dist.sample(size=1000)
        
        assert len(samples) == 1000
        # Lognormal should be positive
        assert all(s > 0 for s in samples)
    
    def test_correlation_matrix_application(self):
        """Test correlation matrix application."""
        # Create two correlated distributions
        distributions = {
            'var1': DistributionConfig(
                dist_type='normal',
                params={'mean': 0.0, 'std': 1.0}
            ),
            'var2': DistributionConfig(
                dist_type='normal',
                params={'mean': 0.0, 'std': 1.0}
            )
        }
        
        # Positive correlation matrix
        correlation_matrix = np.array([[1.0, 0.7], [0.7, 1.0]])
        
        samples = sample_correlated_variables(
            distributions,
            correlation_matrix,
            size=1000
        )
        
        assert 'var1' in samples
        assert 'var2' in samples
        assert len(samples['var1']) == 1000
        assert len(samples['var2']) == 1000
        
        # Check correlation (should be approximately 0.7)
        correlation = np.corrcoef(samples['var1'], samples['var2'])[0, 1]
        assert correlation == pytest.approx(0.7, abs=0.1)
    
    def test_statistical_outputs(self, sample_assumptions_path):
        """Test statistical outputs (mean, median, std dev, percentiles)."""
        config = create_base_case_config(sample_assumptions_path)
        df = run_monte_carlo_simulation(config, num_simulations=100)
        stats = calculate_statistics(df)
        
        assert 'npv' in stats
        assert 'mean' in stats['npv'] or 'median' in stats['npv']
        assert 'irr_with_sale' in stats
        
        for key, value in stats.get('npv', {}).items():
            if isinstance(value, (int, float)):
                assert not np.isnan(value)
                assert not np.isinf(value)
    
    def test_results_within_expected_ranges(self, sample_assumptions_path):
        """Test that results are within expected ranges."""
        config = create_base_case_config(sample_assumptions_path)
        df = run_monte_carlo_simulation(config, num_simulations=100)
        stats = calculate_statistics(df)
        
        mean_irr = stats.get('irr_with_sale', {}).get('mean', 0)
        assert -50.0 < mean_irr < 50.0  # Reasonable IRR range


class TestSampleCorrelatedVariables:
    """Tests for sample_correlated_variables() function."""
    
    def test_correlation_preservation(self):
        """Test that correlation is preserved."""
        distributions = {
            'x': DistributionConfig(
                dist_type='normal',
                params={'mean': 0.0, 'std': 1.0}
            ),
            'y': DistributionConfig(
                dist_type='normal',
                params={'mean': 0.0, 'std': 1.0}
            )
        }
        
        # High positive correlation
        correlation_matrix = np.array([[1.0, 0.9], [0.9, 1.0]])
        
        samples = sample_correlated_variables(
            distributions,
            correlation_matrix,
            size=1000
        )
        
        # Check correlation
        correlation = np.corrcoef(samples['x'], samples['y'])[0, 1]
        assert correlation > 0.8  # Should be close to 0.9
    
    def test_bounds_clipping(self):
        """Test bounds clipping."""
        dist = DistributionConfig(
            dist_type='normal',
            params={'mean': 0.0, 'std': 1.0},
            bounds=(0.0, 1.0)  # Clip to [0, 1]
        )
        
        samples = dist.sample(size=1000)
        
        # All samples should be within bounds
        assert all(0.0 <= s <= 1.0 for s in samples)
    
    def test_cholesky_decomposition_handling(self):
        """Test Cholesky decomposition handling."""
        distributions = {
            'var1': DistributionConfig(
                dist_type='normal',
                params={'mean': 0.0, 'std': 1.0}
            ),
            'var2': DistributionConfig(
                dist_type='normal',
                params={'mean': 0.0, 'std': 1.0}
            )
        }
        
        # Valid correlation matrix (positive semi-definite)
        correlation_matrix = np.array([[1.0, 0.5], [0.5, 1.0]])
        
        # Should not raise error
        samples = sample_correlated_variables(
            distributions,
            correlation_matrix,
            size=100
        )
        
        assert 'var1' in samples
        assert 'var2' in samples


class TestMonteCarloOutput:
    """Tests for Monte Carlo output structure (run_monte_carlo_analysis JSON export)."""
    
    def test_json_export_structure(self, sample_assumptions_path):
        """Test JSON export structure."""
        results = run_monte_carlo_analysis(sample_assumptions_path, 'test_case', n_simulations=100, verbose=False)
        
        assert isinstance(results, dict)
        assert 'statistics' in results
        assert 'timestamp' in results
        assert 'total_simulations' in results
    
    def test_timestamp_present(self, sample_assumptions_path):
        """Test that timestamp is present."""
        results = run_monte_carlo_analysis(sample_assumptions_path, 'test_case', n_simulations=100, verbose=False)
        
        assert 'timestamp' in results
        assert isinstance(results['timestamp'], str)
        assert len(results['timestamp']) > 0
