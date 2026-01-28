"""
Integration tests for full base case analysis workflow
"""

import pytest
import json
import os
from engelberg.analysis import run_base_case_analysis
from engelberg.core import create_base_case_config
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
        
        # Verify required top-level keys
        required_keys = [
            'case_name',
            'timestamp',
            'assumptions',
            'year_1_results',
            'projection',
            'irr_metrics'
        ]
        
        for key in required_keys:
            assert key in json_data, f"Missing key: {key}"
    
    def test_json_export_structure(self, sample_assumptions_path):
        """Test JSON export structure and completeness."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Verify assumptions section
        assert 'assumptions' in json_data
        assumptions = json_data['assumptions']
        assert 'financing' in assumptions
        assert 'rental' in assumptions
        assert 'expenses' in assumptions
        
        # Verify year_1_results section
        assert 'year_1_results' in json_data
        year_1 = json_data['year_1_results']
        assert 'gross_rental_income' in year_1
        assert 'net_operating_income' in year_1
        assert 'cash_flow_per_owner' in year_1
        
        # Verify projection section
        assert 'projection' in json_data
        projection = json_data['projection']
        assert isinstance(projection, list)
        assert len(projection) == 15
        
        # Verify IRR metrics section
        assert 'irr_metrics' in json_data
        irr_metrics = json_data['irr_metrics']
        assert 'equity_irr_with_sale_pct' in irr_metrics
        assert 'moic' in irr_metrics
    
    def test_all_required_kpis_present(self, sample_assumptions_path):
        """Test that all required KPIs are present in results."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Check year_1_results KPIs
        year_1 = json_data['year_1_results']
        kpi_keys = [
            'gross_rental_income',
            'net_operating_income',
            'cash_flow_per_owner',
            'cap_rate_pct',
            'cash_on_cash_return_pct'
        ]
        
        for key in kpi_keys:
            assert key in year_1, f"Missing KPI: {key}"
        
        # Check IRR metrics
        irr_metrics = json_data['irr_metrics']
        irr_keys = [
            'equity_irr_with_sale_pct',
            'project_irr_with_sale_pct',
            'npv_at_5pct',
            'moic'
        ]
        
        for key in irr_keys:
            assert key in irr_metrics, f"Missing IRR metric: {key}"
    
    def test_json_serializable(self, sample_assumptions_path):
        """Test that JSON data is serializable."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        # Should be able to serialize to JSON
        json_string = json.dumps(json_data)
        assert isinstance(json_string, str)
        assert len(json_string) > 0
        
        # Should be able to deserialize
        parsed = json.loads(json_string)
        assert parsed is not None
        assert parsed['case_name'] == 'test_case'
    
    def test_timestamp_present(self, sample_assumptions_path):
        """Test that timestamp is present in JSON export."""
        json_data = run_base_case_analysis(sample_assumptions_path, 'test_case', verbose=False)
        
        assert 'timestamp' in json_data
        timestamp = json_data['timestamp']
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
