"""
Integration tests for full base case analysis workflow
"""

import pytest
import json
import os
from engelberg.analysis import run_base_case_analysis
from engelberg.core import create_base_case_config, get_projection_defaults
from tests.conftest import sample_assumptions_path


class TestBaseCaseAnalysisWorkflow:
    """Tests for full run_base_case_analysis() workflow."""
    
    def test_load_assumptions_from_json(self, sample_assumptions_path):
        """Test loading assumptions from JSON file."""
        config = create_base_case_config(sample_assumptions_path)
        
        assert config is not None
        assert config.financing.purchase_price > 0
        assert config.financing.num_owners > 0
        assert config.rental.seasons is not None
    
    def test_create_configuration(self, sample_assumptions_path):
        """Test configuration creation from assumptions."""
        config = create_base_case_config(sample_assumptions_path)
        
        # Verify all components are present
        assert config.financing is not None
        assert config.rental is not None
        assert config.expenses is not None
        
        # Verify financing parameters
        assert config.financing.purchase_price > 0
        assert 0 < config.financing.ltv <= 1.0
        assert config.financing.interest_rate > 0
        assert config.financing.num_owners > 0
    
    def test_calculate_annual_cash_flows(self, sample_assumptions_path):
        """Test annual cash flows calculation."""
        from engelberg.core import compute_annual_cash_flows
        
        config = create_base_case_config(sample_assumptions_path)
        results = compute_annual_cash_flows(config)
        
        # Verify all required keys are present
        required_keys = [
            'gross_rental_income',
            'net_operating_income',
            'debt_service',
            'cash_flow_per_owner'
        ]
        
        for key in required_keys:
            assert key in results, f"Missing key: {key}"
            assert isinstance(results[key], (int, float))
    
    def test_generate_15_year_projection(self, sample_assumptions_path):
        """Test 15-year projection generation."""
        from engelberg.core import compute_15_year_projection, compute_annual_cash_flows
        
        config = create_base_case_config(sample_assumptions_path)
        projection = compute_15_year_projection(
            config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        # Should have 15 years
        assert len(projection) == 15
        
        # Each year should have required fields
        for year_data in projection:
            assert 'year' in year_data
            assert 'cash_flow_per_owner' in year_data
            assert 'property_value' in year_data
            assert 'remaining_loan_balance' in year_data
    
    def test_calculate_irrs_and_metrics(self, sample_assumptions_path):
        """Test IRR and metrics calculation."""
        from engelberg.core import (
            compute_annual_cash_flows,
            compute_15_year_projection,
            calculate_irrs_from_projection,
            get_projection_defaults
        )
        
        config = create_base_case_config(sample_assumptions_path)
        results = compute_annual_cash_flows(config)
        projection = compute_15_year_projection(
            config,
            start_year=2026,
            inflation_rate=0.01,
            property_appreciation_rate=0.025
        )
        
        proj_defaults = get_projection_defaults(sample_assumptions_path)
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
        
        # Verify all IRR metrics are present
        required_metrics = [
            'equity_irr_with_sale_pct',
            'equity_irr_without_sale_pct',
            'project_irr_with_sale_pct',
            'npv_at_5pct',
            'moic',
            'payback_period_years'
        ]
        
        for metric in required_metrics:
            assert metric in irr_results, f"Missing metric: {metric}"
            assert isinstance(irr_results[metric], (int, float))
    
    def test_full_workflow(self, sample_assumptions_path, temp_output_dir):
        """Test full run_base_case_analysis() workflow."""
        # Run the full analysis
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Verify JSON data structure
        assert json_data is not None
        assert isinstance(json_data, dict)
        
        # Verify required top-level keys (actual export structure)
        required_keys = [
            'config',
            'annual_results',
            'projection_15yr',
            'irr_results',
            'kpis',
            'timestamp',
            'by_horizon'
        ]
        
        for key in required_keys:
            assert key in json_data, f"Missing key: {key}"
        
        # by_horizon: keys "5".."40", each with projection, irr_results, kpis
        by_horizon = json_data['by_horizon']
        for h in ['5', '10', '15', '20', '25', '30', '35', '40']:
            assert h in by_horizon, f"Missing by_horizon[{h}]"
            assert 'projection' in by_horizon[h]
            assert 'irr_results' in by_horizon[h]
            assert 'kpis' in by_horizon[h]
            assert len(by_horizon[h]['projection']) == int(h)
    
    def test_json_export_structure(self, sample_assumptions_path):
        """Test JSON export structure and completeness."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Verify config section
        assert 'config' in json_data
        config = json_data['config']
        assert 'financing' in config
        assert 'rental' in config
        assert 'expenses' in config
        
        # Verify annual_results section
        assert 'annual_results' in json_data
        annual = json_data['annual_results']
        assert 'gross_rental_income' in annual
        assert 'net_operating_income' in annual
        assert 'cash_flow_per_owner' in annual
        
        # Verify projection_15yr (top-level 15-year projection)
        assert 'projection_15yr' in json_data
        projection = json_data['projection_15yr']
        assert isinstance(projection, list)
        assert len(projection) == 15
        
        # Verify irr_results section
        assert 'irr_results' in json_data
        irr_results = json_data['irr_results']
        assert 'equity_irr_with_sale_pct' in irr_results
        assert 'moic' in irr_results
        
        # Verify by_horizon has correct projection lengths
        assert 'by_horizon' in json_data
        for h in ['5', '15', '40']:
            assert len(json_data['by_horizon'][h]['projection']) == int(h)
    
    def test_all_required_kpis_present(self, sample_assumptions_path):
        """Test that all required KPIs are present in results."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Check annual_results KPIs
        annual = json_data['annual_results']
        kpi_keys = [
            'gross_rental_income',
            'net_operating_income',
            'cash_flow_per_owner',
            'cap_rate_pct',
            'cash_on_cash_return_pct'
        ]
        
        for key in kpi_keys:
            assert key in annual, f"Missing KPI: {key}"
        
        # Check irr_results
        irr_results = json_data['irr_results']
        irr_keys = [
            'equity_irr_with_sale_pct',
            'project_irr_with_sale_pct',
            'npv_at_5pct',
            'moic'
        ]
        
        for key in irr_keys:
            assert key in irr_results, f"Missing IRR metric: {key}"
    
    def test_json_serializable(self, sample_assumptions_path):
        """Test that JSON data is serializable."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Should be able to serialize to JSON
        json_string = json.dumps(json_data, default=str)
        assert isinstance(json_string, str)
        assert len(json_string) > 0
        
        # Should be able to deserialize
        parsed = json.loads(json_string)
        assert parsed is not None
        assert 'config' in parsed
        assert 'by_horizon' in parsed
    
    def test_timestamp_present(self, sample_assumptions_path):
        """Test that timestamp is present in JSON export."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        assert 'timestamp' in json_data
        timestamp = json_data['timestamp']
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
    
    def test_rampup_in_json_output(self, sample_assumptions_path):
        """Test that ramp-up metadata is included in JSON export."""
        json_data = run_base_case_analysis(sample_assumptions_path, "test_case", verbose=False)
        
        # Verify ramp-up metadata in annual_results
        annual_results = json_data['annual_results']
        assert 'ramp_up_months' in annual_results, "Ramp-up months should be in annual_results"
        assert 'operational_months' in annual_results, "Operational months should be in annual_results"
        
        # Verify they add up to 12
        ramp_up = annual_results['ramp_up_months']
        operational = annual_results['operational_months']
        assert ramp_up + operational == 12, f"Months should add to 12 (got {ramp_up} + {operational})"
        
        # Verify projection also includes ramp-up info for each horizon
        by_horizon = json_data['by_horizon']
        for horizon_key in ['5', '10', '15', '20']:
            horizon_data = by_horizon[horizon_key]
            projection = horizon_data['projection']
            year1 = projection[0]
            assert 'operational_months' in year1, f"Horizon {horizon_key} Year 1 should have operational_months"
            assert 'ramp_up_months' in year1, f"Horizon {horizon_key} Year 1 should have ramp_up_months"
            
            # Year 2+ should have full operation
            if len(projection) > 1:
                year2 = projection[1]
                assert year2['operational_months'] == 12, f"Horizon {horizon_key} Year 2 should be fully operational"
                assert year2['ramp_up_months'] == 0, f"Horizon {horizon_key} Year 2 should have no ramp-up"
    
    def test_rampup_reduces_year1_revenue(self, sample_assumptions_path):
        """Test that ramp-up period reduces Year 1 revenue proportionally."""
        proj_defaults = get_projection_defaults(sample_assumptions_path)
        ramp_up = proj_defaults.get('ramp_up_months', 0)
        
        if ramp_up > 0:
            json_data = run_base_case_analysis(sample_assumptions_path, "test_case", verbose=False)
            
            annual_results = json_data['annual_results']
            operational_months = annual_results['operational_months']
            
            # Operational months should match ramp-up calculation
            assert operational_months == 12 - ramp_up, f"Operational months should be 12 - {ramp_up} = {12-ramp_up}, got {operational_months}"

    def test_renovation_downtime_in_projection(self, sample_assumptions_path):
        """Test recurring renovation downtime metadata and revenue impact in projection output."""
        json_data = run_base_case_analysis(sample_assumptions_path, "test_case", verbose=False)
        projection = json_data['projection_15yr']

        # Sample assumptions fixture uses renovation every 5 years for 3 months
        year5 = projection[4]
        year4 = projection[3]
        year6 = projection[5]

        assert 'renovation_downtime_months' in year5
        assert year5['renovation_downtime_months'] == 3
        assert year5['operational_months'] == 9
        assert year5['non_operational_months'] == 3
        assert year5['gross_rental_income'] < year4['gross_rental_income']
        assert year5['gross_rental_income'] < year6['gross_rental_income']

    def test_tranche_and_stress_outputs_present(self, sample_assumptions_path):
        """Test tranche mix and SARON stress outputs are exported in analysis payloads."""
        json_data = run_base_case_analysis(sample_assumptions_path, "test_case", verbose=False)

        financing_cfg = json_data["config"]["financing"]
        annual_results = json_data["annual_results"]
        projection_year1 = json_data["projection_15yr"][0]

        assert "loan_tranches" in financing_cfg
        assert len(financing_cfg["loan_tranches"]) == 3
        assert "stress" in financing_cfg
        assert financing_cfg["stress"]["saron_shocks_bps"] == [150, 250]

        assert "blended_interest_rate" in annual_results
        assert "annual_interest_by_tranche" in annual_results
        assert "stress_results" in annual_results
        assert "overall_pass" in annual_results["stress_results"]

        assert "blended_interest_rate" in projection_year1
        assert "annual_interest_by_tranche" in projection_year1
        assert "stress_results" in projection_year1
