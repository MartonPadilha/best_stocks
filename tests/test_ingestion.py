import os
from unittest.mock import patch

import pandas as pd
import pytest

from src import ingestion
from src.ingestion import run_ingestion


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.sqlite")


@pytest.fixture(autouse=True)
def _patch_config_db(db_path, monkeypatch):
    monkeypatch.setattr("src.config.Config.DATABASE", db_path)
    monkeypatch.setattr("config.Config.DATABASE", db_path)


def _collector(df):
    def _main():
        return df
    return _main


def test_run_single_append(db_path):
    df = pd.DataFrame({
        "ticker": ["A", "B"],
        "reference_date": ["2026-01-01", "2026-01-01"],
        "p_l": [10.0, 20.0],
    })
    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.return_value.main = _collector(df)
        summary = run_ingestion(targets=["stock_data"])
    res = summary["results"]["stock_data"]
    assert res["status"] == "success"
    assert res["inserted_rows"] == 2
    assert summary["failed"] is False


def test_run_single_overwrite(db_path):
    df = pd.DataFrame({"ticker": ["A", "B"], "value": [1.0, 2.0]})
    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.return_value.main = _collector(df)
        summary = run_ingestion(targets=["dividends"])
    res = summary["results"]["dividends"]
    assert res["status"] == "success"
    assert res["inserted_rows"] == 2


def test_empty_append_preserves(db_path):
    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.return_value.main = _collector(pd.DataFrame())
        summary = run_ingestion(targets=["stock_data"])
    res = summary["results"]["stock_data"]
    assert res["status"] == "skipped"
    assert res["inserted_rows"] == 0


def test_empty_overwrite_preserves(db_path):
    initial = pd.DataFrame({"ticker": ["A"], "value": [1.0]})
    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.return_value.main = _collector(initial)
        run_ingestion(targets=["dividends"])
    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.return_value.main = _collector(pd.DataFrame())
        summary = run_ingestion(targets=["dividends"])
    res = summary["results"]["dividends"]
    assert res["status"] == "skipped"


def test_news_skipped_when_stock_data_fails(db_path):
    def stock_fail():
        raise RuntimeError("boom")

    news_df = pd.DataFrame({"ticker": ["A"], "url": ["https://x.com/1"], "score": [1]})
    with patch("src.ingestion._load_collector") as mock_loader:
        def loader_side_effect(file_path):
            class M:
                pass
            m = M()
            if "stock_data" in file_path:
                m.main = stock_fail
            else:
                m.main = _collector(news_df)
            return m
        mock_loader.side_effect = loader_side_effect
        summary = run_ingestion(targets=["stock_data", "news"], fail_fast=True)
    assert summary["failed"] is True
    assert summary["results"]["stock_data"]["status"] == "failed"
    assert summary["results"]["news"]["status"] == "skipped"


def test_dependency_order_explicit(db_path):
    call_order = []
    news_df = pd.DataFrame({"ticker": ["A"], "url": ["https://x.com/1"], "score": [1]})

    def loader_side_effect(file_path):
        class M:
            pass
        m = M()
        if "stock_data" in file_path:
            def stock_main():
                call_order.append("stock_data")
                return pd.DataFrame({"ticker": ["A"], "reference_date": ["2026-01-01"]})
            m.main = stock_main
        elif "news" in file_path:
            def news_main():
                call_order.append("news")
                return news_df
            m.main = news_main
        else:
            m.main = _collector(pd.DataFrame())
        return m

    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.side_effect = loader_side_effect
        run_ingestion(targets=["news"])
    assert call_order.index("stock_data") < call_order.index("news")


def test_invalid_target_rejected(db_path):
    with pytest.raises(ValueError):
        run_ingestion(targets=["nonexistent"])


def test_non_dataframe_return_fails(db_path):
    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.return_value.main = lambda: "not a df"
        summary = run_ingestion(targets=["stock_data"])
    assert summary["failed"] is True
    assert "DataFrame" in summary["results"]["stock_data"]["error"]


def test_all_targets_executed_in_order(db_path):
    call_order = []
    def loader_side_effect(file_path):
        class M:
            pass
        m = M()
        name = os.path.splitext(os.path.basename(file_path))[0]
        def make_main(n):
            def _m():
                call_order.append(n)
                if n == "stock_data":
                    return pd.DataFrame({"ticker": ["A"], "reference_date": ["2026-01-01"]})
                if n == "news":
                    return pd.DataFrame({"ticker": ["A"], "url": ["https://x.com/1"], "score": [1]})
                if n == "dividends":
                    return pd.DataFrame({"ticker": ["A"], "value": [1.0]})
                if n == "fii_data":
                    return pd.DataFrame({"ticker": ["ABCD11"], "value": [2.0]})
                return pd.DataFrame()
            return _m
        m.main = make_main(name)
        return m

    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.side_effect = loader_side_effect
        summary = run_ingestion()
    assert call_order.index("stock_data") < call_order.index("news")
    assert summary["failed"] is False
    assert set(summary["results"].keys()) == {"stock_data", "news", "dividends", "fii_data"}


def test_fail_fast_skips_remaining(db_path):
    call_order = []
    def loader_side_effect(file_path):
        class M:
            pass
        m = M()
        name = os.path.basename(file_path)
        if name == "stock_data.py":
            def fail():
                call_order.append("stock_data")
                raise RuntimeError("fail")
            m.main = fail
        else:
            def make_main(n):
                def _m():
                    call_order.append(n)
                    return pd.DataFrame()
                return _m
            m.main = make_main(name)
        return m

    with patch("src.ingestion._load_collector") as mock_loader:
        mock_loader.side_effect = loader_side_effect
        summary = run_ingestion(fail_fast=True)
    assert "news" not in call_order
    assert summary["results"]["news"]["status"] == "skipped"
