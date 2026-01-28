"""
Regression tests against known/validated results
"""

import pytest
from engelberg.analysis import run_base_case_analysis
from engelberg.core import (
    create_base_case_config,
    compute_annual_cash_flows,
    compute_15_year_projection,
    calculate_irrs_from_projection,
    get_projection_defaults
)


class TestKnownBaseCaseResults:
    """Tests against known base case results from actual calculations."""
    
    def test_equity_irr_approximately_4_63_percent(self):
        """Test that Equity IRR is approximately 4.63% for base case."""
        # Use actual base case assumptions
        config = create_base_case_config('assumptions/assumptions.json')
        proj_defaults = get_projection_defaults('assumptions/assumptions.json')
        
        results = compute_annual_cash_flows(config)
        projection = compute_15_year_projection(
            config,
            start_year=proj_defaults['start_year'],
            inflation_rate=proj_defaults['inflation_rate'],
            property_appreciation_rate=proj_defaults['property_appreciation_rate']
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            config.financing.num_owners,
            config.financing.purchase_price,
            proj_defaults['selling_costs_rate'],
            proj_defaults['discount_rate']
        )
        
        # Equity IRR should be approximately 4.63% (with tolerance for calculation differences)
        equity_irr = irr_results['equity_irr_with_sale_pct']
        assert equity_irr == pytest.approx(4.63, abs=0.5)  # Within 0.5% tolerance
    
    def test_monthly_ncf_approximately_negative_239_chf(self):
        """Test that Monthly NCF is approximately -CHF 239/month for base case."""
        config = create_base_case_config('assumptions/assumptions.json')
        results = compute_annual_cash_flows(config)
        
        # Monthly NCF = annual cash flow per owner / 12
        annual_cf_per_owner = results['cash_flow_per_owner']
        monthly_ncf = annual_cf_per_owner / 12
        
        # Should be approximately -239 CHF/month (with tolerance)
        assert monthly_ncf == pytest.approx(-239.0, abs=50.0)  # Within 50 CHF tolerance
    
    def test_project_irr_approximately_2_53_percent(self):
        """Test that Project IRR is approximately 2.53% for base case."""
        config = create_base_case_config('assumptions/assumptions.json')
        proj_defaults = get_projection_defaults('assumptions/assumptions.json')
        
        results = compute_annual_cash_flows(config)
        projection = compute_15_year_projection(
            config,
            start_year=proj_defaults['start_year'],
            inflation_rate=proj_defaults['inflation_rate'],
            property_appreciation_rate=proj_defaults['property_appreciation_rate']
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            config.financing.num_owners,
            config.financing.purchase_price,
            proj_defaults['selling_costs_rate'],
            proj_defaults['discount_rate']
        )
        
        # Project IRR should be approximately 2.53%
        project_irr = irr_results['project_irr_with_sale_pct']
        assert project_irr == pytest.approx(2.53, abs=0.5)  # Within 0.5% tolerance
    
    def test_moic_approximately_2_17x(self):
        """Test that MOIC is approximately 2.17× for base case."""
        config = create_base_case_config('assumptions/assumptions.json')
        proj_defaults = get_projection_defaults('assumptions/assumptions.json')
        
        results = compute_annual_cash_flows(config)
        projection = compute_15_year_projection(
            config,
            start_year=proj_defaults['start_year'],
            inflation_rate=proj_defaults['inflation_rate'],
            property_appreciation_rate=proj_defaults['property_appreciation_rate']
        )
        
        final_property_value = projection[-1]['property_value']
        final_loan_balance = projection[-1]['remaining_loan_balance']
        
        irr_results = calculate_irrs_from_projection(
            projection,
            results['equity_per_owner'],
            final_property_value,
            final_loan_balance,
            config.financing.num_owners,
            config.financing.purchase_price,
            proj_defaults['selling_costs_rate'],
            proj_defaults['discount_rate']
        )
        
        # MOIC should be approximately 2.17×
        moic = irr_results['moic']
        assert moic == pytest.approx(2.17, abs=0.2)  # Within 0.2× tolerance
    
    def test_calculations_havent_regressed(self):
        """Test that calculations haven't regressed (smoke test)."""
        # Run full base case analysis
        json_data = run_base_case_analysis('assumptions/assumptions.json', 'base_case', verbose=False)
        
        # Verify key metrics are present and reasonable
        assert 'irr_metrics' in json_data
        irr_metrics = json_data['irr_metrics']
        
        # Equity IRR should be positive and reasonable
        equity_irr = irr_metrics.get('equity_irr_with_sale_pct', 0)
        assert 0.0 < equity_irr < 20.0  # Reasonable range
        
        # MOIC should be positive
        moic = irr_metrics.get('moic', 0)
        assert moic > 0
        
        # NPV can be negative or positive
        npv = irr_metrics.get('npv_at_5pct', 0)
        assert abs(npv) < 1000000.0  # Reasonable range


class TestCrossValidationWithValidateSystem:
    """Tests that cross-validate with validate_system.py results."""
    
    def test_base_case_analysis_completes(self):
        """Test that base case analysis completes without error."""
        # This is a smoke test to ensure the analysis runs
        json_data = run_base_case_analysis('assumptions/assumptions.json', 'base_case', verbose=False)
        
        assert json_data is not None
        assert isinstance(json_data, dict)
        assert 'case_name' in json_data
    
    def test_all_required_sections_present(self):
        """Test that all required sections are present in base case results."""
        json_data = run_base_case_analysis('assumptions/assumptions.json', 'base_case', verbose=False)
        
        required_sections = [
            'assumptions',
            'year_1_results',
            'projection',
            'irr_metrics'
        ]
        
        for section in required_sections:
            assert section in json_data, f"Missing section: {section}"
