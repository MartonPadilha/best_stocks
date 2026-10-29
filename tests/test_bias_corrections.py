import numpy as np
import pandas as pd
import pytest

from src.analysis import Calcs
from src.profiles import build_config
from src.stock_app import analysis_tickers
from src.config import Config


@pytest.fixture
def weights():
    return {
        "roe": {"weight": 0.20, "normalization": "default"},
        "roic": {"weight": 0.20, "normalization": "default"},
        "p_l": {"weight": 0.20, "normalization": "inverter_zero"},
        "dy": {"weight": 0.20, "normalization": "default"},
        "m_líquida": {"weight": 0.20, "normalization": "default"},
    }


def test_reconcile_roe_roic_penalizes_spread(weights):
    calcs = Calcs(weights)
    df = pd.DataFrame({
        "ticker": ["A", "B", "C"],
        "roe": [35.0, 15.0, 40.0],
        "roic": [9.0, 12.0, 38.0],
        "p_l": [10, 10, 10],
        "dy": [5, 5, 5],
        "m_líquida": [10, 10, 10],
    })
    out = calcs.reconcile_roe_roic(df)
    # A: spread 26 → penalizado; B: spread 3 → ok; C: spread 2 → ok
    assert out.loc[out["ticker"] == "A", "roe_roic_penalty"].iloc[0] < out.loc[out["ticker"] == "B", "roe_roic_penalty"].iloc[0]
    assert out.loc[out["ticker"] == "C", "roe_roic_penalty"].iloc[0] > out.loc[out["ticker"] == "A", "roe_roic_penalty"].iloc[0]


def test_reconcile_roe_roic_missing_returns_neutral(weights):
    calcs = Calcs(weights)
    df = pd.DataFrame({"ticker": ["A"], "roe": [np.nan], "roic": [np.nan]})
    out = calcs.reconcile_roe_roic(df)
    assert out["roe_roic_penalty"].iloc[0] == 1.0


def test_compute_trend_detects_decline(weights):
    calcs = Calcs(weights)
    dates = pd.date_range("2026-01-01", periods=6, freq="ME")
    df = pd.DataFrame({
        "ticker": ["A"] * 6,
        "reference_date": dates,
        "roe": [30, 28, 25, 20, 15, 10],
        "roic": [20, 18, 15, 12, 9, 6],
    })
    trend = calcs.compute_trend(df, ["roe", "roic"])
    row = trend[trend["ticker"] == "A"].iloc[0]
    assert row["trend_roe"] < 0
    assert row["trend_roic"] < 0


def test_compute_trend_stable_returns_near_zero(weights):
    calcs = Calcs(weights)
    dates = pd.date_range("2026-01-01", periods=6, freq="ME")
    df = pd.DataFrame({
        "ticker": ["A"] * 6,
        "reference_date": dates,
        "roe": [20, 20, 20, 20, 20, 20],
    })
    trend = calcs.compute_trend(df, ["roe"])
    assert abs(trend["trend_roe"].iloc[0]) < 0.05


def test_dy_value_trap_detected(weights):
    calcs = Calcs(weights)
    dates = pd.date_range("2026-01-01", periods=10, freq="ME")
    df = pd.DataFrame({
        "ticker": ["VULC3"] * 10,
        "reference_date": dates,
        "dy": [8, 8, 9, 10, 12, 13, 15, 18, 22, 26],
        "p_vp": [2.5, 2.4, 2.3, 2.1, 2.0, 1.8, 1.7, 1.6, 1.5, 1.44],
    })
    trap = calcs.detect_dy_value_trap(df)
    row = trap[trap["ticker"] == "VULC3"].iloc[0]
    assert row["dy_value_trap_flag"] is True or bool(row["dy_value_trap_flag"]) is True
    assert row["dy_trap_penalty"] < 1.0


def test_dy_value_trap_not_triggered_for_stable(weights):
    calcs = Calcs(weights)
    dates = pd.date_range("2026-01-01", periods=6, freq="ME")
    df = pd.DataFrame({
        "ticker": ["GOOD"] * 6,
        "reference_date": dates,
        "dy": [5, 5, 5, 5, 5, 5],
        "p_vp": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
    })
    trap = calcs.detect_dy_value_trap(df)
    row = trap[trap["ticker"] == "GOOD"].iloc[0]
    assert bool(row["dy_value_trap_flag"]) is False
    assert row["dy_trap_penalty"] == 1.0


def test_robust_normalize_missing_becomes_neutral(weights):
    calcs = Calcs(weights)
    df = pd.DataFrame({
        "ticker": ["A", "B", "C", "D"],
        "roe": [10, 20, np.nan, 15],
        "p_l": [10, 15, 12, np.nan],
        "dy": [5, 7, 6, 8],
        "m_líquida": [10, 12, 11, 13],
        "roic": [8, 15, 10, 12],
    })
    out = calcs.robust_normalize(df, list(weights.keys()))
    # NaN deve virar 0.5 (neutro), não 0 (pior)
    assert out.loc[out["ticker"] == "C", "roe"].iloc[0] == pytest.approx(0.5)
    assert out.loc[out["ticker"] == "D", "p_l"].iloc[0] == pytest.approx(0.5)


def test_sector_analyses_excludes_unhealthy_peers(weights):
    calcs = Calcs(weights)
    # Setor com 4 saudáveis e 2 com prejuízo
    df = pd.DataFrame({
        "ticker": ["H1", "H2", "H3", "H4", "U1", "U2"],
        "sector": ["X"] * 6,
        "roe": [15, 18, 20, 22, -10, -5],
        "roic": [10, 12, 15, 18, -8, -3],
        "p_l": [10, 12, 15, 18, -5, -2],
        "dy": [5, 6, 7, 8, 0, 0],
        "m_líquida": [10, 12, 15, 18, -5, -3],
    })
    out = calcs.sector_analyses(df, list(weights.keys()))
    # Empresas não-saudáveis não devem liderar o score setorial
    healthy_scores = out[out["ticker"].isin(["H1", "H2", "H3", "H4"])]["score_sector"]
    unhealthy_scores = out[out["ticker"].isin(["U1", "U2"])]["score_sector"]
    assert healthy_scores.max() > unhealthy_scores.max()


def test_vulc3_not_first_after_corrections(monkeypatch):
    """Teste integrador: constrói histórico que simula VULC3 (ROE alto, ROIC caindo, DY subindo por preço caindo)
    e verifica que ele não lidera o ranking após as correções."""
    dates = pd.date_range("2026-01-01", periods=10, freq="ME")
    rows = []
    for i, d in enumerate(dates):
        # VULC3: ROE 35 (constante), ROIC caindo de 22→9 (spread crescente), DY subindo 8→26, P/VP caindo 2.5→1.44
        rows.append({"ticker": "VULC3", "reference_date": d, "type": "stock", "sector": "Cons",
                     "p_l": 4.1, "p_vp": max(1.44, 2.5 - (2.5 - 1.44) * i / 9),
                     "roe": 35, "roic": max(9.4, 22 - (22 - 9.4) * i / 9),
                     "dy": min(26, 8 + (26 - 8) * i / 9),
                     "m_líquida": 24.9, "dív_líquida_ebitda": 0.7, "cagr_lucros_5_anos": 96,
                     "cagr_receitas_5_anos": 24, "liq_corrente": 2.9, "passivos_ativos": 0.36, "lpa": 2.0})
    for i, d in enumerate(dates):
        # GOOD4: ROE 20, ROIC 18 (spread saudável estável), DY estável 6, P/VP estável 2.0
        rows.append({"ticker": "GOOD4", "reference_date": d, "type": "stock", "sector": "Cons",
                     "p_l": 12, "p_vp": 2.0, "roe": 20, "roic": 18, "dy": 6,
                     "m_líquida": 15, "dív_líquida_ebitda": 0.5, "cagr_lucros_5_anos": 15,
                     "cagr_receitas_5_anos": 12, "liq_corrente": 2.0, "passivos_ativos": 0.4, "lpa": 1.5})
    hist = pd.DataFrame(rows)

    def fake_view(self):
        return hist.copy()
    monkeypatch.setattr("src.stock_app.Database.view", fake_view)
    monkeypatch.setattr("src.stock_app.fetch_momentum_bulk", lambda t, days=90: pd.DataFrame({"ticker": t, "momentum": 0.0}))

    cfg = build_config("Equilibrado", momentum_override=0.0)
    calcs = Calcs(cfg.weights, temporal_windows=cfg.temporal_windows, winsor_limits=cfg.winsor_limits)
    df, _ = analysis_tickers("stock", calcs, analysis_config=cfg)

    assert not df.empty
    leader = df.iloc[0]["ticker"]
    # VULC3 não deve ser o líder após correções
    assert leader != "VULC3", f"VULC3 ainda é #1; score_final={df.iloc[0]['score_final']}"
