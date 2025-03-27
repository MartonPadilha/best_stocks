import requests
from bs4 import BeautifulSoup
import pandas as pd
import ast
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
   
def parse_dividend_table(html, ticker):
    """ Extract and process divendend's table. """
    
    reference_date = pd.to_datetime(datetime.date.today())
    try:
        div_list_content = html.find("div", class_="list-content")
        if not div_list_content:
            return 

        table = div_list_content.find("table")
        if not table:
            return

        headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
        rows = []
        for tr in table.find("tbody").find_all("tr"):
            rows.append([td.get_text(strip=True) for td in tr.find_all("td")])

        df = pd.DataFrame(rows, columns=headers)
        df['ticker'] = ticker
        df['data_compra'] = pd.to_datetime(df['DATA COM'], format='%d/%m/%Y')
        df = df[df['data_compra'] > reference_date]
        
        return df if not df.empty else None

    except Exception as e:
        print(f"Error in {ticker}: {e}")
        return
    
def read_list(path):
    
    with open(path, 'r') as file:
        file_list = ast.literal_eval(file.read())
    
    return file_list

def main():
    list_stocks = read_list(LIST_PATH)
    data_frames = []

    for ticker in tqdm(list_stocks, desc="Processing tickers"):

        if ticker.endswith('11'):
            continue
        elif ticker[-2:].isdigit() and int(ticker[-2:]) >= 32:
            continue
        else:
            html = fetch_html(ticker)
            if html:
                df = parse_dividend_table(html, ticker)
                if df is not None:
                    data_frames.append(df)
    
    final_df = pd.concat(data_frames, ignore_index = True)

    return final_df

if __name__ == "__main__":
    main()