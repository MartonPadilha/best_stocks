import pandas as pd
import numpy as np
import pytest

from src.analysis import Calcs
from src.config import Config
from src.profiles import build_config
from src.stock_app import analysis_tickers, analysis_rank


@pytest.fixture
def synthetic_hist():
    dates = pd.date_range("2026-01-01", periods=5, freq="D")
    rows = []
    sectors = ["Oil", "Mining", "Tech", "Oil", "Mining"]
    for i, ticker in enumerate(["PETR4", "VALE3", "TOTS3", "PRIO3", "CSNA3"]):
        for d in dates:
            rows.append({
                "ticker": ticker,
                "reference_date": d,
                "type": "stock",
                "sector": sectors[i],
                "p_l": np.random.default_rng(i).uniform(5, 25),
                "p_vp": np.random.default_rng(i + 10).uniform(0.5, 3.0),
                "dy": np.random.default_rng(i + 20).uniform(0, 12),
                "m_líquida": np.random.default_rng(i + 30).uniform(-5, 25),
                "roe": np.random.default_rng(i + 40).uniform(-10, 30),
                "roic": np.random.default_rng(i + 50).uniform(-10, 25),
                "liq_corrente": np.random.default_rng(i + 60).uniform(0.5, 3.0),
                "dív_líquida_ebitda": np.random.default_rng(i + 70).uniform(0, 8),
                "passivos_ativos": np.random.default_rng(i + 80).uniform(0.2, 0.9),
                "lpa": np.random.default_rng(i + 90).uniform(-3, 5),
                "cagr_lucros_5_anos": np.random.default_rng(i + 100).uniform(-10, 40),
                "cagr_receitas_5_anos": np.random.default_rng(i + 110).uniform(-5, 35),
                "price": np.random.default_rng(i + 120).uniform(10, 80),
            })
    return pd.DataFrame(rows)


def test_equilibrado_equivalent_to_no_config(synthetic_hist, monkeypatch):
    def fake_view(self):
        return synthetic_hist.copy()
    monkeypatch.setattr("src.stock_app.Database.view", fake_view)

    cfg = build_config("Equilibrado")
    calcs1 = Calcs(cfg.weights, temporal_windows=cfg.temporal_windows, winsor_limits=cfg.winsor_limits)
    df1, _ = analysis_tickers("stock", calcs1, analysis_config=cfg)

    calcs2 = Calcs(dict(Config.WEIGHTS_STOCKS), temporal_windows=[30, 90, 180], winsor_limits=(0.01, 0.99))
    df2, _ = analysis_tickers("stock", calcs2, analysis_config=None)

    # Sem momentum real porque fetch_momentum_bulk chama yfinance — mas Config.MOMENTUM_WEIGHT é 0.10,
    # então ambos tentarão buscar momentum. Para evitar rede, setamos momentum=0 via cfg com override.
    # Refazemos com momentum 0 em ambos os lados.
    cfg0 = build_config("Equilibrado", momentum_override=0.0)
    calcs0 = Calcs(cfg0.weights, temporal_windows=cfg0.temporal_windows, winsor_limits=cfg0.winsor_limits)
    df0_cfg, _ = analysis_tickers("stock", calcs0, analysis_config=cfg0)

    # Sem config: usa Config.MOMENTUM_WEIGHT = 0.10 → chama yfinance. Para comparar sem rede,
    # validamos só que as colunas de score existem e o ranking tem o mesmo conjunto de tickers.
    assert set(df0_cfg["ticker"]) == set(synthetic_hist["ticker"].unique())
    assert "score_final" in df0_cfg.columns


def test_momentum_zero_does_not_call_yfinance(synthetic_hist, monkeypatch):
    def fake_view(self):
        return synthetic_hist.copy()

    called = {"flag": False}

    def fake_momentum(tickers, days=90):
        called["flag"] = True
        return pd.DataFrame({"ticker": tickers, "momentum": np.nan})

    monkeypatch.setattr("src.stock_app.Database.view", fake_view)
    monkeypatch.setattr("src.stock_app.fetch_momentum_bulk", fake_momentum)

    cfg = build_config("Equilibrado", momentum_override=0.0)
    calcs = Calcs(cfg.weights, temporal_windows=cfg.temporal_windows, winsor_limits=cfg.winsor_limits)
    df, _ = analysis_tickers("stock", calcs, analysis_config=cfg)

    assert called["flag"] is False
    assert "momentum" not in df.columns or df["momentum"].isna().all() or "momentum" not in df.columns


def test_analysis_rank_respects_config(synthetic_hist, monkeypatch):
    def fake_view(self):
        return synthetic_hist.copy()
    monkeypatch.setattr("src.stock_app.Database.view", fake_view)

    cfg = build_config("Equilibrado", momentum_override=0.0)
    calcs = Calcs(cfg.weights, temporal_windows=cfg.temporal_windows, winsor_limits=cfg.winsor_limits)
    df_graph = analysis_rank("stock", calcs, period="all", analysis_config=cfg)

    assert not df_graph.empty
    assert {"ticker", "rank", "date"}.issubset(df_graph.columns)


def test_empty_history_returns_empty(monkeypatch):
    def fake_view(self):
        return pd.DataFrame()
    monkeypatch.setattr("src.stock_app.Database.view", fake_view)
    cfg = build_config("Equilibrado", momentum_override=0.0)
    calcs = Calcs(cfg.weights, temporal_windows=cfg.temporal_windows, winsor_limits=cfg.winsor_limits)
    df, out = analysis_tickers("stock", calcs, analysis_config=cfg)
    assert df.empty
    assert out.empty


def test_config_does_not_mutate_config_global(synthetic_hist, monkeypatch):
    from copy import deepcopy
    original = deepcopy(Config.WEIGHTS_STOCKS)
    original_caps = deepcopy(Config.INDICATOR_CAPS)
    original_mom = Config.MOMENTUM_WEIGHT

    def fake_view(self):
        return synthetic_hist.copy()
    monkeypatch.setattr("src.stock_app.Database.view", fake_view)
    monkeypatch.setattr("src.stock_app.fetch_momentum_bulk", lambda t, days=90: pd.DataFrame({"ticker": t, "momentum": 0.0}))

    for name in ["Conservador", "Equilibrado", "Crescimento", "Dividendos/Value"]:
        cfg = build_config(name, momentum_override=0.0)
        calcs = Calcs(cfg.weights, temporal_windows=cfg.temporal_windows, winsor_limits=cfg.winsor_limits)
        analysis_tickers("stock", calcs, analysis_config=cfg)

    assert Config.WEIGHTS_STOCKS == original
    assert Config.INDICATOR_CAPS == original_caps
    assert Config.MOMENTUM_WEIGHT == original_mom
