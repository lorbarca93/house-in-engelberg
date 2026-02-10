"""
Integration tests for loan structure sensitivity analysis workflow.
"""

import pytest

from engelberg.analysis import run_loan_structure_sensitivity_analysis


class TestLoanStructureSensitivityAnalysis:
    """Tests for run_loan_structure_sensitivity_analysis()."""

    def test_output_shape_and_required_scenarios(self, sample_assumptions_path):
        json_data = run_loan_structure_sensitivity_analysis(
            sample_assumptions_path,
            "test_case",
            verbose=False,
        )

        assert json_data["analysis_type"] == "loan_structure_sensitivity"
        assert "scenarios" in json_data
        assert isinstance(json_data["scenarios"], list)
        assert len(json_data["scenarios"]) >= 6
        assert "stress_policy" in json_data
        assert "base_dscr_min" in json_data["stress_policy"]
        assert "saron_150_dscr_min" in json_data["stress_policy"]
        assert "saron_250_min_cash_flow" in json_data["stress_policy"]

        scenario_ids = {scenario["id"] for scenario in json_data["scenarios"]}
        assert {
            "saron_100",
            "fixed_100_10y",
            "fixed_staggered_50_50",
            "mixed_50_50",
            "mixed_60_40_laddered",
            "mixed_70_30",
        }.issubset(scenario_ids)

    def test_tranche_weights_and_kpis(self, sample_assumptions_path):
        json_data = run_loan_structure_sensitivity_analysis(
            sample_assumptions_path,
            "test_case",
            verbose=False,
        )

        for scenario in json_data["scenarios"]:
            total_share = sum(
                float(tranche.get("share_of_loan", 0.0))
                for tranche in scenario.get("loan_tranches", [])
            )
            assert total_share == pytest.approx(1.0, rel=1e-6)

            kpis = scenario["kpis"]
            for key in [
                "blended_interest_rate",
                "year1_debt_service",
                "year1_after_tax_cash_flow_per_owner_monthly",
                "equity_irr_with_sale_pct",
                "year1_dscr",
                "stress_dscr_base",
                "stress_dscr_saron_150bps",
                "stress_dscr_saron_250bps",
                "stress_overall_pass",
                "has_saron_exposure",
            ]:
                assert key in kpis

        fixed_100 = next(
            scenario for scenario in json_data["scenarios"] if scenario["id"] == "fixed_100_10y"
        )
        fixed_kpis = fixed_100["kpis"]
        assert fixed_kpis["has_saron_exposure"] is False
        assert fixed_kpis["stress_dscr_saron_150bps"] == pytest.approx(
            fixed_kpis["stress_dscr_base"],
            rel=1e-6,
        )
        assert fixed_kpis["stress_dscr_saron_250bps"] == pytest.approx(
            fixed_kpis["stress_dscr_base"],
            rel=1e-6,
        )

    def test_rankings_recommendation_and_wealth_components(self, sample_assumptions_path):
        json_data = run_loan_structure_sensitivity_analysis(
            sample_assumptions_path,
            "test_case",
            verbose=False,
        )

        scenario_ids = {scenario["id"] for scenario in json_data["scenarios"]}
        assert json_data["recommended_scenario_id"] in scenario_ids

        ranking = json_data["ranking"]
        assert set(ranking["by_equity_irr_desc"]).issubset(scenario_ids)
        assert set(ranking["by_monthly_cashflow_desc"]).issubset(scenario_ids)

        for scenario in json_data["scenarios"]:
            equity_build = scenario["equity_build_5y"]
            assert "cash_flow_after_tax_per_owner" in equity_build
            assert "amortization_per_owner" in equity_build
            assert "property_appreciation_per_owner" in equity_build
            assert "net_wealth_creation_per_owner" in equity_build

            expected_net_wealth = (
                float(equity_build["cash_flow_after_tax_per_owner"])
                + float(equity_build["amortization_per_owner"])
                + float(equity_build["property_appreciation_per_owner"])
            )
            assert float(equity_build["net_wealth_creation_per_owner"]) == pytest.approx(
                expected_net_wealth,
                rel=1e-6,
            )
