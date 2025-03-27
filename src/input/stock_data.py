import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import ast
import yfinance as yf
import numpy as np
import datetime
from tqdm import tqdm

HEADER = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
URL_BASE = f'https://statusinvest.com.br/'
LIST_PATH = 'storage/tickers_list.txt'

def fetch_html(ticker):
    """ Gets HTML of the StatusInvest page for the given ticker. """
    
    url = f"{URL_BASE}/acoes/{ticker}"
    try:
        response = requests.get(url, headers=HEADER, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException as e:
        print(f"Error in {ticker}: {e}")
        return
    
def parse_indicators(html, ticker):
    try:
        company_sector_infos = html.find_all('div', class_ = re.compile('card bg-main-gd-h white-text rounded ov-hidden pt-0 pb-0'))[0]
        company_sector_info = company_sector_infos.find_all('div', class_ = re.compile('info '))
        sector = []
        for sector_info in company_sector_info:
            a = sector_info.find('a', class_ = 'white-text d-flex')
            info = a.find('strong', class_ = 'value').get_text()
            sector.append(info)

        company = html.find('h1', class_ = 'lh-4').get_text()
        card = html.find_all('div', class_ = 'indicator-today-container')[0]
        data_group = card.find_all('div', class_ = re.compile('indicators '))

        dic_indicators = {
            'sector': [],
            'ticker': [],
            'name': [],
            'value': []
        }

        for break_one in data_group:

            items = break_one.find_all('div', class_ = re.compile(' item'))
            for item in items:  
                item_name = item.find('h3', class_ = re.compile('title ')).get_text()
                item_value = item.find('strong', class_ = re.compile('value ')).get_text()
                dic_indicators['sector'].append(sector[1])
                dic_indicators['ticker'].append(company[:5])
                dic_indicators['name'].append(item_name)
                dic_indicators['value'].append(item_value)

        return pd.DataFrame(dic_indicators)
        
    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")
        return None
    
def clean_data(df):
    if df is not None:
        df['value'] = df['value'].str.replace('%', '').str.replace('.', '').str.replace(',', '.')
        df['value'] = df['value'].apply(lambda x: '0' if x == '-' else x).astype(float)
        df['name'] = df['name'].str.replace(' ', '_').str.replace('/', '_').str.replace('.', '').str.lower()

        return df
    
def get_yfinance_data(ticker):
    dados = []
    error = []
    try:
        info = yf.Ticker(ticker + '.SA').info
        dados.append({
            'ticker': ticker,
            'sector': info.get('sector', ''),
            'p_l': info.get('forwardPE', np.nan),
            'p_vp': info.get('priceToBook', np.nan),
            'dividend_yield': (info.get('dividendYield', np.nan)) * 100,
            'crescimento_lucro': (info.get('earningsGrowth', np.nan)) * 100,
            'roe': (info.get('returnOnEquity', np.nan)) * 100,
            'payout_ratio': info.get("payoutRatio", np.nan),
        })
    except Exception as e:
        print(ticker)
        error.append(ticker[:4])
        print(f"Erro ao buscar {ticker}: {e}")

    return pd.DataFrame(dados)


def read_list(path):
    
    with open(path, 'r') as file:
        file_list = ast.literal_eval(file.read())
    
    return file_list

def main():
    data_frames = []
    list_stocks = read_list(LIST_PATH)

    for ticker in tqdm(list_stocks, desc="Processing tickers"):

        if ticker.endswith('11'):
            # df_fii = get_yfinance_data(ticker)
            # print(df_fii)
            # return
            continue
        elif ticker[-2:].isdigit() and int(ticker[-2:]) >= 32:
            continue
        else:
            html = fetch_html(ticker)
            if html:
                df = parse_indicators(html, ticker)
                df = clean_data(df)
                df['type'] = 'stock'
                if df is not None:
                    data_frames.append(df)
                
    final_df = pd.concat(data_frames, ignore_index = True)
    
    final_df = final_df.pivot_table(
        index=['sector', 'ticker', 'type'],
        columns='name', 
        values='value', 
        aggfunc='first'
    ).reset_index()
    
    final_df['reference_date'] = datetime.date.today()
    
    return final_df

if __name__ == "__main__":
    main()