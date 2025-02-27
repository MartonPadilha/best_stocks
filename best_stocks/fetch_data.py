import yfinance as yf
import pandas as pd
from database import Database
from config import Config
import ast
import numpy as np

LIST_PATH = 'list_stocks.txt'
db = Database(Config.DATABASE['name'], Config.DATABASE['table'])

def read_list(path):
    
    with open(path, 'r') as file:
        file_list = ast.literal_eval(file.read())
    
    return file_list

def get_stock_data(_list):
    dados = []
    error = []
    
    for code in _list:
        try:
            info = yf.Ticker(code + '.SA').info
            dados.append({
                'ticker': code,
                'sector': info.get('sector', ''),
                'p_l': info.get('forwardPE', np.nan),
                'p_vp': info.get('priceToBook', np.nan),
                'dividend_yield': (info.get('dividendYield', np.nan)) * 100,
                'crescimento_lucro': (info.get('earningsGrowth', np.nan)) * 100,
                'roe': (info.get('returnOnEquity', np.nan)) * 100,
                'payout_ratio': info.get("payoutRatio", np.nan),
            })
        except Exception as e:
            print(code)
            error.append(code[:4])
            print(f"Erro ao buscar {code}: {e}")

    return pd.DataFrame(dados)

def main():
    df = db.view()
    if df is None:
        list_stocks = read_list(LIST_PATH)
        df_stock = get_stock_data(list_stocks)
        db.create(df_stock)
        df = db.view()
    
    return df

if __name__ == "__main__":
    main()

