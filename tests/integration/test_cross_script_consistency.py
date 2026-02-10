"""
Cross-script and cross-output consistency tests.

These tests validate that:
1) Input assumptions and exported outputs stay aligned.
2) Analysis JSON files are mutually consistent (base/sensitivity/coc/ncf/loan).
3) Different script entry points produce consistent results.
"""

import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

import engelberg.analysis as analysis_module
import engelberg.mc_sensitivity as mc_sensitivity_module
import engelberg.model_sensitivity as model_sensitivity_module
from engelberg.core import create_base_case_config, resolve_path
from scripts import generate_all_data as generate_all_data_module


REQUIRED_DATA_FILE_KEYS = [
    "base_case_analysis",
    "sensitivity",
    "sensitivity_coc",
    "sensitivity_ncf",
    "monte_carlo",
    "loan_structure_sensitivity",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _assumptions_path_for_case(case_entry):
    assumptions_file = case_entry["assumptions_file"]
    candidate_paths = [
        Path(resolve_path(f"assumptions/{assumptions_file}")),
        Path(resolve_path(assumptions_file)),
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve assumptions file for case: {case_entry}")


def _data_path_for_case(case_entry, key):
    filename = case_entry["data_files"][key]
    return Path(resolve_path(f"website/data/{filename}"))


def _run_analysis_main_cli(monkeypatch, assumptions_path, analysis_type, simulations=120):
    argv = [
        "analyze.py",
        str(assumptions_path),
        "--analysis",
        analysis_type,
        "--quiet",
    ]
    if analysis_type in {"monte_carlo", "monte_carlo_sensitivity", "all"}:
        argv.extend(["--simulations", str(simulations)])
    monkeypatch.setattr(sys, "argv", argv)
    analysis_module.main()


@pytest.fixture
def cases_index_data():
    index_path = Path(resolve_path("website/data/cases_index.json"))
    return _load_json(index_path)


@pytest.fixture
def redirected_output_root(monkeypatch, tmp_path):
    """
    Redirect data output paths used by analysis and batch scripts to a temp root.
    """
    sandbox_root = tmp_path / "sandbox_project"

    def sandbox_resolve_path(relative_path):
        normalized = relative_path.replace("/", os.sep)
        return str(sandbox_root / normalized)

    monkeypatch.setattr(analysis_module, "resolve_path", sandbox_resolve_path)
    monkeypatch.setattr(
        model_sensitivity_module,
        "resolve_path",
        sandbox_resolve_path,
    )
    monkeypatch.setattr(
        mc_sensitivity_module,
        "resolve_path",
        sandbox_resolve_path,
    )
    monkeypatch.setattr(
        generate_all_data_module,
        "resolve_path",
        sandbox_resolve_path,
    )
    return sandbox_root


class TestCasesIndexAndFiles:
    def test_cases_index_has_required_data_links(self, cases_index_data):
        assert "cases" in cases_index_data
        assert isinstance(cases_index_data["cases"], list)
        assert len(cases_index_data["cases"]) > 0

        for case_entry in cases_index_data["cases"]:
            case_name = case_entry["case_name"]
            data_files = case_entry.get("data_files", {})

            for key in REQUIRED_DATA_FILE_KEYS:
                assert key in data_files, f"{case_name}: missing data_files[{key}]"
                assert data_files[key], f"{case_name}: empty data_files[{key}]"
                assert data_files[key].startswith(f"{case_name}_"), (
                    f"{case_name}: data file naming mismatch for {key}: "
                    f"{data_files[key]}"
                )

            for key, filename in data_files.items():
                if not filename:
                    continue
                data_path = Path(resolve_path(f"website/data/{filename}"))
                assert data_path.exists(), f"{case_name}: missing file {filename}"

            assumptions_path = _assumptions_path_for_case(case_entry)
            assert assumptions_path.exists()


class TestInputToOutputConsistency:
    def test_base_case_outputs_match_assumptions_config(self, cases_index_data):
        for case_entry in cases_index_data["cases"]:
            assumptions_path = _assumptions_path_for_case(case_entry)
            config = create_base_case_config(str(assumptions_path))
            base_output = _load_json(_data_path_for_case(case_entry, "base_case_analysis"))

            financing_out = base_output["config"]["financing"]
            financing_cfg = config.financing

            assert financing_out["purchase_price"] == pytest.approx(
                financing_cfg.purchase_price, rel=1e-10
            )
            assert financing_out["ltv"] == pytest.approx(financing_cfg.ltv, rel=1e-10)
            assert financing_out["interest_rate"] == pytest.approx(
                financing_cfg.interest_rate, rel=1e-10
            )
            assert financing_out["amortization_rate"] == pytest.approx(
                financing_cfg.amortization_rate, rel=1e-10
            )
            assert financing_out["num_owners"] == financing_cfg.num_owners
            assert financing_out["loan_amount"] == pytest.approx(
                financing_cfg.loan_amount, rel=1e-10
            )
            assert financing_out["equity_total"] == pytest.approx(
                financing_cfg.equity_total, rel=1e-10
            )

            expenses_out = base_output["config"]["expenses"]
            expenses_cfg = config.expenses
            assert expenses_out["property_management_fee_rate"] == pytest.approx(
                expenses_cfg.property_management_fee_rate, rel=1e-10
            )
            assert expenses_out["average_length_of_stay"] == pytest.approx(
                expenses_cfg.average_length_of_stay, rel=1e-10
            )
            assert expenses_out["maintenance_rate"] == pytest.approx(
                expenses_cfg.maintenance_rate, rel=1e-10
            )

    def test_base_case_output_internal_identities(self, cases_index_data):
        for case_entry in cases_index_data["cases"]:
            base_output = _load_json(_data_path_for_case(case_entry, "base_case_analysis"))
            annual = base_output["annual_results"]
            year1 = base_output["projection_15yr"][0]
            num_owners = base_output["config"]["financing"]["num_owners"]

            assert annual["debt_service"] == pytest.approx(
                annual["interest_payment"] + annual["amortization_payment"],
                rel=1e-10,
            )
            assert annual["cash_flow_after_debt_service"] == pytest.approx(
                annual["net_operating_income"] - annual["debt_service"],
                rel=1e-10,
            )
            assert annual["cash_flow_per_owner"] == pytest.approx(
                annual["cash_flow_after_debt_service"] / max(num_owners, 1),
                rel=1e-10,
            )
            assert annual["after_tax_cash_flow_total"] == pytest.approx(
                annual["cash_flow_after_debt_service"] + annual["tax_savings_total"],
                rel=1e-10,
            )
            assert annual["after_tax_cash_flow_per_owner"] == pytest.approx(
                annual["after_tax_cash_flow_total"] / max(num_owners, 1),
                rel=1e-10,
            )

            # Year-1 projection should mirror annual results for core flow metrics.
            for field in [
                "gross_rental_income",
                "net_operating_income",
                "interest_payment",
                "amortization_payment",
                "debt_service",
                "cash_flow_per_owner",
            ]:
                assert year1[field] == pytest.approx(annual[field], rel=1e-10)


class TestCrossAnalysisConsistency:
    def test_analysis_files_align_for_each_case(self, cases_index_data):
        for case_entry in cases_index_data["cases"]:
            sensitivity_output = _load_json(_data_path_for_case(case_entry, "sensitivity"))
            coc_output = _load_json(_data_path_for_case(case_entry, "sensitivity_coc"))
            ncf_output = _load_json(_data_path_for_case(case_entry, "sensitivity_ncf"))
            loan_output = _load_json(
                _data_path_for_case(case_entry, "loan_structure_sensitivity")
            )

            base_irr = sensitivity_output["base_irr"]
            for parameter in sensitivity_output.get("sensitivities", []):
                assert parameter["base_irr"] == pytest.approx(base_irr, rel=1e-12)

            base_coc = coc_output["base_coc"]
            for parameter in coc_output.get("sensitivities", []):
                assert parameter["base_irr"] == pytest.approx(base_coc, rel=1e-12)

            base_ncf = ncf_output["base_ncf"]
            for parameter in ncf_output.get("sensitivities", []):
                assert parameter["base_irr"] == pytest.approx(base_ncf, rel=1e-12)

            by_horizon = ncf_output.get("by_horizon", {})
            if by_horizon:
                for horizon_payload in by_horizon.values():
                    assert horizon_payload["base_ncf"] == pytest.approx(base_ncf, rel=1e-12)
                    assert len(horizon_payload.get("sensitivities", [])) == len(
                        ncf_output.get("sensitivities", [])
                    )

            scenario_ids = {scenario["id"] for scenario in loan_output["scenarios"]}
            assert loan_output["recommended_scenario_id"] in scenario_ids
            assert set(loan_output["ranking"]["by_equity_irr_desc"]).issubset(scenario_ids)
            assert set(loan_output["ranking"]["by_monthly_cashflow_desc"]).issubset(
                scenario_ids
            )

            for scenario in loan_output["scenarios"]:
                kpis = scenario["kpis"]
                has_saron = kpis["has_saron_exposure"]
                tranche_has_saron = any(
                    tranche.get("rate_type") == "saron"
                    for tranche in scenario.get("loan_tranches", [])
                )
                assert has_saron == tranche_has_saron

                if not has_saron:
                    assert kpis["stress_dscr_saron_150bps"] == pytest.approx(
                        kpis["stress_dscr_base"], rel=1e-10
                    )
                    assert kpis["stress_dscr_saron_250bps"] == pytest.approx(
                        kpis["stress_dscr_base"], rel=1e-10
                    )


class TestScriptEntryPointConsistency:
    def test_analyze_main_and_generate_case_data_are_consistent(
        self,
        monkeypatch,
        tmp_path,
        sample_assumptions_path,
        redirected_output_root,
    ):
        assumptions_path = tmp_path / "assumptions_cross_script.json"
        shutil.copyfile(sample_assumptions_path, assumptions_path)
        case_name = analysis_module.extract_case_name(str(assumptions_path))

        # Run script-style analysis orchestration via engelberg.analysis.main().
        _run_analysis_main_cli(monkeypatch, assumptions_path, "base")
        _run_analysis_main_cli(monkeypatch, assumptions_path, "sensitivity")
        np.random.seed(42)
        _run_analysis_main_cli(
            monkeypatch,
            assumptions_path,
            "monte_carlo",
            simulations=120,
        )
        _run_analysis_main_cli(monkeypatch, assumptions_path, "loan_structure_sensitivity")

        data_dir = redirected_output_root / "website" / "data"
        main_base = _load_json(data_dir / f"{case_name}_base_case_analysis.json")
        main_sensitivity = _load_json(data_dir / f"{case_name}_sensitivity.json")
        main_mc = _load_json(data_dir / f"{case_name}_monte_carlo.json")
        main_loan = _load_json(
            data_dir / f"{case_name}_loan_structure_sensitivity.json"
        )

        metadata = generate_all_data_module.get_case_metadata(str(assumptions_path))

        # Re-run through batch generator and compare key outputs.
        np.random.seed(42)
        batch_result = generate_all_data_module.generate_case_data(
            case_name=case_name,
            assumptions_path=str(assumptions_path),
            case_metadata=metadata,
            monte_carlo_simulations=120,
            include_mc_sensitivity=False,
        )

        assert batch_result["status"] == "success"
        for key in REQUIRED_DATA_FILE_KEYS:
            assert batch_result[key], f"Batch output missing {key}"

        batch_base = _load_json(data_dir / f"{case_name}_base_case_analysis.json")
        batch_sensitivity = _load_json(data_dir / f"{case_name}_sensitivity.json")
        batch_mc = _load_json(data_dir / f"{case_name}_monte_carlo.json")
        batch_loan = _load_json(
            data_dir / f"{case_name}_loan_structure_sensitivity.json"
        )

        assert batch_base["irr_results"]["equity_irr_with_sale_pct"] == pytest.approx(
            main_base["irr_results"]["equity_irr_with_sale_pct"], rel=1e-10
        )
        assert batch_base["annual_results"]["after_tax_cash_flow_per_owner"] == pytest.approx(
            main_base["annual_results"]["after_tax_cash_flow_per_owner"], rel=1e-10
        )
        assert batch_sensitivity["base_irr"] == pytest.approx(
            main_sensitivity["base_irr"], rel=1e-10
        )
        assert batch_loan["recommended_scenario_id"] == main_loan["recommended_scenario_id"]

        # Monte Carlo is stochastic; enforce configuration-level and range consistency.
        assert batch_mc["total_simulations"] == 120
        assert main_mc["total_simulations"] == 120

        main_npv_mean = float(main_mc["statistics"]["npv"]["mean"])
        batch_npv_mean = float(batch_mc["statistics"]["npv"]["mean"])
        main_npv_std = float(main_mc["statistics"]["npv"]["std"])
        batch_npv_std = float(batch_mc["statistics"]["npv"]["std"])
        npv_tolerance = max(main_npv_std, batch_npv_std)
        assert abs(main_npv_mean - batch_npv_mean) <= npv_tolerance

        main_irr_mean = float(main_mc["statistics"]["irr_with_sale"]["mean"])
        batch_irr_mean = float(batch_mc["statistics"]["irr_with_sale"]["mean"])
        main_irr_std = float(main_mc["statistics"]["irr_with_sale"]["std"])
        batch_irr_std = float(batch_mc["statistics"]["irr_with_sale"]["std"])
        irr_tolerance = max(main_irr_std, batch_irr_std)
        assert abs(main_irr_mean - batch_irr_mean) <= irr_tolerance
