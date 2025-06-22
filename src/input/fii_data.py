import re
import pandas as pd
import ast
import yfinance as yf
import numpy as np
import datetime as dt
from tqdm import tqdm

LIST_PATH = 'storage/tickers_list.txt'
GARBAGE_LIST = 'storage/fii_tickers_error.txt'
now = dt.datetime.now()
date_filter = f"{now.year - 1}-{str(now.month).zfill(2)}-01"

all_data = []
tickers_error = []

def read_list(path):
    with open(path, 'r') as file:
        file_list = ast.literal_eval(file.read())
    return file_list

def get_yfinance_data(ticker):
    ticker += '.SA'
    data = yf.Ticker(ticker)
    dividends = data.dividends

    df = pd.DataFrame(dividends.reset_index())
    df = df[df['Date'] >= date_filter]
    df['ticker'] = ticker[:-3]
    df['current_price'] = data.info['previousClose']

    result = df.groupby('ticker').agg(
        total_dividends=('Dividends', 'sum'),
        last_dividends=('Dividends', 'last'),
        last_current_price=('current_price', 'first'),
    ).reset_index()

    result['last_dividend_yield'] = (result['last_dividends'] / result['last_current_price']) * 100
    result['total_dividend_yield'] = (result['total_dividends'] / result['last_current_price']) * 100

    return result

def join_dataframes(df):
    return pd.concat(all_data, ignore_index=True)

def main():
    list_stocks = read_list(LIST_PATH)
    garbage_list = read_list(GARBAGE_LIST)
    tickers = [i for i in list_stocks if i.endswith('11') and i not in garbage_list]
    for ticker in tqdm(tickers, desc="Processing tickers.."):
        try:
            result = get_yfinance_data(ticker)
            all_data.append(result)
        except Exception as e:
            tickers_error.append(ticker)
            continue

    final_df = join_dataframes(all_data)
    return final_df

if __name__ == "__main__":
    main()

