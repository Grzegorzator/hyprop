"""Tests for hyprop.export and hyprop.database (synthetic result)."""

import pytest

from hyprop.core.config import EngineConfig
from hyprop.database import list_records, load_engine, save_engine, save_record
from hyprop.export import export_result, generate_report
from hyprop.oppoints import analyze
from tests.test_oppoints import _synthetic
from tests.test_solver import CFG


@pytest.fixture(scope="module")
def bundle():
    result = _synthetic()
    result.summary = dict(burn_time_s=12.0, total_impulse_ns=5000.0,
                          peak_thrust_n=500.0, peak_pc_pa=30e5,
                          propellant_used_kg=2.3, isp_mean_s=200.0)
    return EngineConfig.from_dict(CFG), result, analyze(result)


def test_export_tables(tmp_path, bundle):
    config, result, rop = bundle
    files = export_result(result, tmp_path, config=config, rop=rop)
    names = {f.name for f in files}
    assert {"run_history.csv", "run_history.json", "run.xlsx",
            "run_rop_points.csv", "run_phases.csv",
            "run_config.yaml"} <= names
    import pandas as pd
    frame = pd.read_csv(tmp_path / "run_history.csv")
    assert "thrust" in frame.columns and len(frame) > 100


def test_generate_report_tex(tmp_path, bundle):
    config, result, rop = bundle
    out = generate_report(config, result, rop, tmp_path / "report",
                          compile_pdf=False)
    tex = out.read_text(encoding="utf-8")
    assert out.suffix == ".tex"
    for anchor in (r"\section{Representative Operating Points}",
                   "impulse-weighted", r"\section{Mission Requirements}",
                   r"\end{document}"):
        assert anchor in tex


def test_database_roundtrip(tmp_path, bundle):
    config, result, _ = bundle
    save_engine(config, result.summary, root=tmp_path)
    loaded, summary = load_engine(config.name, root=tmp_path)
    assert loaded == config
    assert summary["total_impulse_ns"] == 5000.0
    assert config.name in list_records("engines", root=tmp_path)
    save_record("materials", "graphite_eg", {"k_w_mk": 90.0}, root=tmp_path)
    assert "graphite_eg" in list_records("materials", root=tmp_path)
