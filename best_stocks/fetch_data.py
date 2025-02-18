import yfinance as yf
import pandas as pd
from best_stocks.database import Database
from best_stocks.config import Config
import ast

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
        print(code)
        try:
            info = yf.Ticker(code + '.SA').info
            dados.append({
                'ticker': code,
                'sector': info.get('sector', ''),
                'p_l': info.get('forwardPE', 0) or 0,
                'p_vp': info.get('priceToBook', 0) or 0,
                'dividend_yield': (info.get('dividendYield', 0) or 0) * 100,
                'crescimento_lucro': (info.get('earningsGrowth', 0) or 0) * 100,
                'roe': (info.get('returnOnEquity', 0) or 0) * 100,
                'payout_ratio': info.get("payoutRatio") or 0,
            })
        except Exception as e:
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

