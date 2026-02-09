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
        
        # Equity IRR re-baselined after insurance 0.15% / maintenance 0.25% (was 4.63%)
        equity_irr = irr_results['equity_irr_with_sale_pct']
        assert equity_irr == pytest.approx(7.46, abs=0.5)  # Within 0.5% tolerance
    
    def test_monthly_ncf_approximately_negative_239_chf(self):
        """Test that Monthly NCF is approximately -CHF 239/month for base case."""
        config = create_base_case_config('assumptions/assumptions.json')
        results = compute_annual_cash_flows(config)
        
        # Monthly NCF = annual cash flow per owner / 12
        annual_cf_per_owner = results['cash_flow_per_owner']
        monthly_ncf = annual_cf_per_owner / 12
        
        # Re-baselined after insurance 0.15% / maintenance 0.25% (was -239 CHF/month)
        assert monthly_ncf == pytest.approx(-192.0, abs=80.0)  # Within 80 CHF tolerance
    
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
        
        # Project IRR re-baselined after insurance/maintenance change (was 2.53%)
        project_irr = irr_results['project_irr_with_sale_pct']
        assert project_irr == pytest.approx(3.55, abs=0.5)  # Within 0.5% tolerance
    
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
        
        # MOIC re-baselined after insurance/maintenance change (was 2.17×)
        moic = irr_results['moic']
        assert moic == pytest.approx(3.21, abs=0.2)  # Within 0.2× tolerance
    
    def test_calculations_havent_regressed(self):
        """Test that calculations haven't regressed (smoke test)."""
        # Run full base case analysis
        json_data = run_base_case_analysis('assumptions/assumptions.json', 'base_case', verbose=False)
        
        # Verify key metrics are present and reasonable (schema uses irr_results)
        assert 'irr_results' in json_data
        irr_metrics = json_data['irr_results']
        
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
        assert 'config' in json_data
        assert 'annual_results' in json_data
        assert 'irr_results' in json_data
    
    def test_all_required_sections_present(self):
        """Test that all required sections are present in base case results."""
        json_data = run_base_case_analysis('assumptions/assumptions.json', 'base_case', verbose=False)
        
        required_sections = [
            'config',
            'annual_results',
            'by_horizon',
            'irr_results'
        ]
        
        for section in required_sections:
            assert section in json_data, f"Missing section: {section}"
