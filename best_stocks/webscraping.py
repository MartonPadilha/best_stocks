import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from database import Database
from config import Config
import ast

HEADER = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
URL_BASE = f'https://statusinvest.com.br/'
LIST_PATH = 'list_stocks.txt'
db = Database(Config.DATABASE['name'], Config.DATABASE['table'])

def fetch_html(ticker):
    url = f"{URL_BASE}/acoes/{ticker}" if not ticker.endswith("11") else f"{URL_BASE}/fundos-imobiliarios/{ticker}"
    response = requests.get(url, headers=HEADER)
    if response.status_code == 200:
        return BeautifulSoup(response.content, "html.parser")
    else:
        return print('Error to get HTML')
    
def parse_html(soup, ticker):
    try:
        company_sector_infos = soup.find_all('div', class_ = re.compile('card bg-main-gd-h white-text rounded ov-hidden pt-0 pb-0'))[0]
        company_sector_info = company_sector_infos.find_all('div', class_ = re.compile('info '))
        sector = []
        for sector_info in company_sector_info:
            a = sector_info.find('a', class_ = 'white-text d-flex')
            info = a.find('strong', class_ = 'value').get_text()
            sector.append(info)

        company = soup.find('h1', class_ = 'lh-4').get_text()
        card = soup.find_all('div', class_ = 'indicator-today-container')[0]
        data_group = card.find_all('div', class_ = re.compile('indicators '))

        dic_indicators = {
            'activity': [],
            'activity_subsector': [],
            'business_segment': [],
            'company_code': [],
            'company_name': [],
            'type': [],
            'name': [],
            'value': []
        }

        for break_one in data_group:
            indicators_type = break_one.find('strong', class_ = 'd-block uppercase').get_text()

            items = break_one.find_all('div', class_ = re.compile(' item'))
            for item in items:  
                item_name = item.find('h3', class_ = re.compile('title ')).get_text()
                item_value = item.find('strong', class_ = re.compile('value ')).get_text()
                dic_indicators['business_segment'].append(sector[3])
                dic_indicators['activity_subsector'].append(sector[2])
                dic_indicators['activity'].append(sector[1])
                dic_indicators['company_code'].append(company[:5])
                dic_indicators['company_name'].append(company[8:])
                dic_indicators['type'].append(indicators_type)
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

        df = df.pivot_table(index=['business_segment', 'activity_subsector', 'activity', 'company_code', 'company_name'],
                            columns='name', values='value', aggfunc='first').reset_index()
        
        df.rename(columns={
            'company_code': 'ticker',
            'activity': 'sector',
            'P/L': 'p_l',
            'P/VP': 'p_vp',
            'D.Y': 'dividend_yield',
            'CAGR Lucros 5 anos': 'crescimento_lucro',
            'CAGR Receitas 5 anos': 'crescimento_receita',
            'M. Líquida': 'm_liquida',
            'LPA': 'lpa',
            'Dív. líquida/EBITDA': 'div_liq_ebitda',
            'Liq. corrente': 'liq_corrent',
            'P/Ativo': 'passivos_ativos',
            'ROE': 'roe'
        }, inplace=True)

        return df

def read_list(path):
    
    with open(path, 'r') as file:
        file_list = ast.literal_eval(file.read())
    
    return file_list

def main():
    df = db.view()
    
    if df is None or df.empty:
        list_stocks = read_list(LIST_PATH)
        data_frames = [clean_data(parse_html(fetch_html(stock), stock)) for stock in list_stocks]
        df_stock = pd.concat([df for df in data_frames if df is not None])
        db.create(df_stock)
        df = db.view()
    
    return df

if __name__ == "__main__":
    main()
