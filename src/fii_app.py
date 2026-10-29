from database import Database
from config import Config
import pandas as pd

TABLE_NAME = 'fii_data'

FII_NOTICE = (
    "O ranking multifatorial de FIIs ainda não está implementado. "
    "Esta tela exibe apenas os dados disponíveis na base e não calcula "
    "uma classificação equivalente à de ações."
)


def show_fiis():
    df_base = Database(TABLE_NAME, Config.DATABASE).view()
    return df_base


def filter_fiis(df, ticker=None):
    if df is None or df.empty:
        return df
    out = df
    if ticker:
        out = out[out['ticker'].astype(str).str.contains(ticker, case=False, na=False)]
    return out
