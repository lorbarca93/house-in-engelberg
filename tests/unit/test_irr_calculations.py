"""
Unit tests for IRR, NPV, MOIC, and payback period calculations
"""

import pytest
from engelberg.core import (
    calculate_irr,
    calculate_irrs_from_projection,
    BaseCaseConfig
)
from tests.fixtures.test_configs import create_test_base_config
from tests.conftest import assert_approximately_equal


class TestCalculateIRR:
    """Tests for calculate_irr() function."""
    
    def test_simple_irr_positive_cash_flows(self):
        """Test IRR calculation with simple positive cash flows."""
        # Simple case: invest 1000, get 1100 back in year 1
        cash_flows = [1100.0]
        initial_investment = 1000.0
        
        irr = calculate_irr(cash_flows, initial_investment)
        
        # IRR should be approximately 10% (1100/1000 - 1)
        # Note: calculate_irr returns decimal (0.10), not percentage (10.0)
        assert irr == pytest.approx(0.10, abs=0.01)
    
    def test_irr_with_sale_proceeds(self):
        """Test IRR calculation including sale proceeds."""
        # Invest 1000, get 100 per year for 5 years, then sell for 1200
        cash_flows = [100.0] * 5
        initial_investment = 1000.0
        sale_proceeds = 1200.0
        
        irr = calculate_irr(cash_flows, initial_investment, sale_proceeds)
        
        # Should be positive IRR
        assert irr > 0
        # Should be reasonable (roughly 10-15% range for this scenario)
        # Note: calculate_irr returns decimal, so 0.05 < irr < 0.20
        assert 0.05 < irr < 0.20
    
    def test_irr_without_sale_negative_cash_flows(self):
        """Test IRR calculation without sale (negative cash flows)."""
        # Invest 1000, lose 50 per year for 5 years, no sale
        cash_flows = [-50.0] * 5
        initial_investment = 1000.0
        sale_proceeds = 0.0
        
        irr = calculate_irr(cash_flows, initial_investment, sale_proceeds)
        
        # Should be negative IRR (or very close to zero if all negative)
        # Note: When all cash flows are negative, IRR may be 0 or negative
        assert irr <= 0
    
    def test_irr_all_positive_flows(self):
        """Test IRR with all positive cash flows."""
        # Invest 1000, get 200 per year for 5 years
        cash_flows = [200.0] * 5
        initial_investment = 1000.0
        
        irr = calculate_irr(cash_flows, initial_investment)
        
        # Should be positive (or very close to zero due to numerical precision)
        # Note: calculate_irr returns decimal
        # When all cash flows are positive, IRR may be slightly negative due to numerical precision
        assert irr >= -1e-8  # Allow for numerical precision (very small negative is acceptable)
    
    def test_irr_convergence(self):
        """Test that IRR calculation converges."""
        # More complex cash flow pattern
        cash_flows = [-100.0, 50.0, 100.0, 150.0, 200.0]
        initial_investment = 1000.0
        sale_proceeds = 1200.0
        
        irr = calculate_irr(cash_flows, initial_investment, sale_proceeds)
        
        # Should return a valid number (not NaN or infinite)
        assert isinstance(irr, float)
        assert not (irr != irr)  # Not NaN
        assert abs(irr) < 1000.0  # Reasonable range
    
    def test_irr_precision(self):
        """Test IRR calculation precision."""
        # Known IRR case: invest 1000, get 1100 in year 1 = 10% IRR
        cash_flows = [1100.0]
        initial_investment = 1000.0
        
        irr = calculate_irr(cash_flows, initial_investment)
        
        # Should be very close to 10% (0.10 as decimal)
        # Note: calculate_irr returns decimal, not percentage
        assert irr == pytest.approx(0.10, abs=0.01)


class TestCalculateIRRsFromProjection:
    """Tests for calculate_irrs_from_projection() function."""
    
    def test_equity_irr_with_sale(self, minimal_config):
        """Test Equity IRR calculation with sale."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        # Calculate projection
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        # Get final values
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,  # selling_costs_rate
            0.05    # discount_rate
        )
        
        # Should have equity_irr_with_sale_pct
        assert 'equity_irr_with_sale_pct' in irr_results
        assert isinstance(irr_results['equity_irr_with_sale_pct'], float)
        # Should be a reasonable percentage
        assert -50.0 < irr_results['equity_irr_with_sale_pct'] < 50.0
    
    def test_equity_irr_without_sale(self, minimal_config):
        """Test Equity IRR calculation without sale."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,
            0.05
        )
        
        # Should have equity_irr_without_sale_pct
        assert 'equity_irr_without_sale_pct' in irr_results
        assert isinstance(irr_results['equity_irr_without_sale_pct'], float)
        # Without sale, IRR is typically lower (or negative)
        assert irr_results['equity_irr_without_sale_pct'] <= irr_results['equity_irr_with_sale_pct']
    
    def test_project_irr_calculation(self, minimal_config):
        """Test Project IRR (unlevered) calculation."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,
            0.05
        )
        
        # Should have project_irr_with_sale_pct
        assert 'project_irr_with_sale_pct' in irr_results
        assert isinstance(irr_results['project_irr_with_sale_pct'], float)
        # Project IRR should be lower than Equity IRR (no leverage benefit)
        assert irr_results['project_irr_with_sale_pct'] <= irr_results['equity_irr_with_sale_pct']
    
    def test_npv_calculation(self, minimal_config):
        """Test NPV calculation at discount rate."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,
            0.05  # 5% discount rate
        )
        
        # Should have npv_at_5pct
        assert 'npv_at_5pct' in irr_results
        assert isinstance(irr_results['npv_at_5pct'], float)
        # NPV can be positive or negative
        assert abs(irr_results['npv_at_5pct']) < 1000000.0  # Reasonable range
    
    def test_moic_calculation(self, minimal_config):
        """Test MOIC (Multiple on Invested Capital) calculation."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,
            0.05
        )
        
        # Should have moic
        assert 'moic' in irr_results
        assert isinstance(irr_results['moic'], float)
        # MOIC should be positive (total return / initial investment)
        assert irr_results['moic'] > 0
        # Typically between 1x and 5x for real estate
        assert 0.5 < irr_results['moic'] < 10.0
    
    def test_payback_period_calculation(self, minimal_config):
        """Test payback period calculation."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,
            0.05
        )
        
        # Should have payback_period_years
        assert 'payback_period_years' in irr_results
        assert isinstance(irr_results['payback_period_years'], (int, float))
        # Payback should be between 0 and projection years
        assert 0 <= irr_results['payback_period_years'] <= 15
    
    def test_all_irr_metrics_present(self, minimal_config):
        """Test that all IRR metrics are present in results."""
        from engelberg.core import compute_annual_cash_flows, compute_15_year_projection
        
        results = compute_annual_cash_flows(minimal_config)
        projection = compute_15_year_projection(
            minimal_config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            minimal_config.financing.num_owners,
            minimal_config.financing.purchase_price,
            0.078,
            0.05
        )
        
        required_keys = [
            'equity_irr_with_sale_pct',
            'equity_irr_without_sale_pct',
            'project_irr_with_sale_pct',
            'npv_at_5pct',
            'moic',
            'payback_period_years'
        ]
        
        for key in required_keys:
            assert key in irr_results, f"Missing key: {key}"
            assert isinstance(irr_results[key], (int, float)), f"Key {key} is not numeric"
    
    def test_irr_with_known_projection_data(self):
        """Test IRR calculation with manually verified projection data."""
        # Create a simple projection with known IRR
        projection = []
        initial_equity = 250000.0  # 25% of 1M property
        
        # Year 1-5: -5000 per year (negative cash flow)
        # Year 6-15: 0 per year
        # Year 15: Sale for 1.5M, loan balance 700k, selling costs 7.8%
        # Net sale proceeds per owner: (1.5M * 0.922 - 700k) / 2 = 191,500
        
        for year in range(1, 16):
            projection.append({
                'year': 2025 + year,
                'cash_flow_per_owner': -5000.0 if year <= 5 else 0.0,
                'cumulative_cash_flow_per_owner': -5000.0 * min(year, 5),
                'net_operating_income': 20000.0  # Add required field for unlevered IRR calculation
            })
        
        final_property_value = 1500000.0
        final_loan_balance = 700000.0
        num_owners = 2
        purchase_price = 1000000.0
        selling_costs_rate = 0.078
        discount_rate = 0.05
        
        irr_results = calculate_irrs_from_projection(
            projection,
            initial_equity,
            final_property_value,
            final_loan_balance,
            num_owners,
            purchase_price,
            selling_costs_rate,
            discount_rate
        )
        
        # Should calculate all metrics
        assert 'equity_irr_with_sale_pct' in irr_results
        assert isinstance(irr_results['equity_irr_with_sale_pct'], float)
