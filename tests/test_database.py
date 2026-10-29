import os
import tempfile

import pandas as pd
import pytest

from src.database import Database


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.sqlite")


@pytest.fixture
def stocks_df():
    return pd.DataFrame({
        "ticker": ["PETR4", "VALE3", "ABCD4"],
        "reference_date": ["2026-01-01", "2026-01-01", "2026-01-01"],
        "sector": ["Oil", "Mining", "Tech"],
        "p_l": [10.0, 12.0, 20.0],
    })


@pytest.fixture
def news_df():
    return pd.DataFrame({
        "ticker": ["PETR4", "VALE3"],
        "url": ["https://ex.com/a", "https://ex.com/b"],
        "date": ["2026-01-01", "2026-01-01"],
        "summary": ["s1", "s2"],
        "score": [1, -1],
    })


def test_append_creates_table(db_path, stocks_df):
    db = Database("stock_data", db_path)
    res = db.append_if_new(stocks_df, ["ticker", "reference_date"])
    assert res["inserted_rows"] == 3
    assert db.count_rows() == 3


def test_append_empty_preserves(db_path, stocks_df):
    db = Database("stock_data", db_path)
    db.append_if_new(stocks_df, ["ticker", "reference_date"])
    res = db.append_if_new(pd.DataFrame(), ["ticker", "reference_date"])
    assert res["skipped"] is True
    assert res["inserted_rows"] == 0
    assert db.count_rows() == 3


def test_append_idempotent(db_path, stocks_df):
    db = Database("stock_data", db_path)
    db.append_if_new(stocks_df, ["ticker", "reference_date"])
    res = db.append_if_new(stocks_df, ["ticker", "reference_date"])
    assert res["inserted_rows"] == 0
    assert db.count_rows() == 3


def test_append_new_rows_only(db_path, stocks_df):
    db = Database("stock_data", db_path)
    db.append_if_new(stocks_df, ["ticker", "reference_date"])
    new = pd.DataFrame({
        "ticker": ["PETR4", "KEPL3"],
        "reference_date": ["2026-01-01", "2026-01-01"],
        "sector": ["Oil", "Tech"],
        "p_l": [10.0, 5.0],
    })
    res = db.append_if_new(new, ["ticker", "reference_date"])
    assert res["inserted_rows"] == 1
    assert db.count_rows() == 4


def test_append_composite_key_no_collision(db_path):
    db = Database("t", db_path)
    df = pd.DataFrame({
        "a": ["AB", "A"],
        "b": ["12", "B12"],
        "v": [1, 2],
    })
    db.append_if_new(df, ["a", "b"])
    again = pd.DataFrame({
        "a": ["AB", "A"],
        "b": ["12", "B12"],
        "v": [99, 99],
    })
    res = db.append_if_new(again, ["a", "b"])
    assert res["inserted_rows"] == 0
    assert db.count_rows() == 2


def test_append_rejects_null_keys(db_path):
    db = Database("news", db_path)
    df = pd.DataFrame({
        "ticker": ["A", "B"],
        "url": ["https://x.com/1", None],
        "score": [1, 2],
    })
    res = db.append_if_new(df, ["url"])
    assert res["inserted_rows"] == 1
    assert res["rejected_rows"] == 1
    assert db.count_rows() == 1


def test_append_does_not_mutate_input(db_path, stocks_df):
    db = Database("stock_data", db_path)
    cols_before = list(stocks_df.columns)
    db.append_if_new(stocks_df, ["ticker", "reference_date"])
    assert list(stocks_df.columns) == cols_before


def test_replace_overwrites(db_path):
    db = Database("dividends", db_path)
    db.replace_if_non_empty(pd.DataFrame({"ticker": ["A", "B"], "value": [1.0, 2.0]}))
    assert db.count_rows() == 2
    db.replace_if_non_empty(pd.DataFrame({"ticker": ["C"], "value": [3.0]}))
    assert db.count_rows() == 1


def test_replace_empty_preserves(db_path):
    db = Database("dividends", db_path)
    db.replace_if_non_empty(pd.DataFrame({"ticker": ["A", "B"], "value": [1.0, 2.0]}))
    res = db.replace_if_non_empty(pd.DataFrame())
    assert res["skipped"] is True
    assert db.count_rows() == 2


def test_table_exists(db_path, stocks_df):
    db = Database("stock_data", db_path)
    assert db.table_exists() is False
    db.append_if_new(stocks_df, ["ticker", "reference_date"])
    assert db.table_exists() is True


def test_append_auto_adds_missing_columns(db_path):
    db = Database("stock_data", db_path)
    initial = pd.DataFrame({
        "ticker": ["A"],
        "reference_date": ["2026-01-01"],
        "sector": ["Oil"],
    })
    db.append_if_new(initial, ["ticker", "reference_date"])
    cols = {row[1] for row in __import__("sqlite3").connect(db_path).execute("PRAGMA table_info(stock_data)").fetchall()}
    assert "type" not in cols

    with_new_col = pd.DataFrame({
        "ticker": ["B"],
        "reference_date": ["2026-01-02"],
        "sector": ["Mining"],
        "type": ["stock"],
        "p_l": [15.0],
    })
    res = db.append_if_new(with_new_col, ["ticker", "reference_date"])
    assert res["inserted_rows"] == 1
    cols = {row[1] for row in __import__("sqlite3").connect(db_path).execute("PRAGMA table_info(stock_data)").fetchall()}
    assert "type" in cols
    assert "p_l" in cols
