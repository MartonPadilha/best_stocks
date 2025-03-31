import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import google.generativeai as genai
from datetime import datetime, timedelta
from database import Database
from config import Config
import numpy as np
from tqdm import tqdm

load_dotenv()

class News():
    def __init__(self, ticker):
        self.api_key = os.getenv("TOKEN_NEWS")
        self.ticker = ticker
        self.url = f'https://newsapi.org/v2/everything?q={self.ticker}&apiKey={self.api_key}'
    
    def get_news(self):
        try:
            response = requests.get(self.url)
            data = response.json()

            news = []
            for article in data['articles']:
                item = {
                    'title': article['title'],
                    'description': article['description'],
                    'date': article['publishedAt'],
                    'url': article['url']
                }
                news.append(item)
            
            return news
        except Exception as e:
            print(f'Error fetching news for {self.ticker}: {e}')
            return
        
    def get_full_article(self, url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            paragraph = soup.find_all('p')
            full_text = ' '.join([p.get_text() for p in paragraph])
            
            return full_text
        else:
            return "Não foi possível obter a notícia."

    
    def openai(self, news):
        
        prompt = f"""Em um parágrafo, avalie a notícia abaixo de acordo com sua qualidade geral e impacto positivo ou negativo no para a empresa no mercado financeiro.
                Dê uma nota de -2 a 2, considerando:
                -2: A notícia é extremamente negativa e prejudicial, com um impacto sério e imediato para empresa ou mercado financeiro.
                -1: A notícia é negativa, mas com um impacto moderado ou de longo prazo, que pode gerar alguma preocupação para empresa ou mercado financeiro.
                0: A notícia é neutra, sem impacto significativo, positivo ou negativo.
                1: A notícia é positiva, com um impacto positivo e um benefício moderado para para empresa ou mercado financeiro.
                2: A notícia é extremamente positiva, com impacto muito favorável, podendo gerar grandes ganhos ou um grande impulso para empresa ou mercado financeiro.

                Leve em consideração os seguintes aspectos:
                1. Aspectos econômicos/financeiros
                2. Expectativas do mercado
                3. Impacto de longo prazo
                4. Tons e intenções

                A seguir, a notícia para avaliação:
                {news}

                OBRIGATÓRIO: No final, escreva "A nota é: (SUA_NOTA)"
                ps: ignore anuncios e textos relativos a publicação do artigo.
                """
        google_key = os.getenv("TOKEN_GOOGLEAI")
        genai.configure(api_key=google_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        return response.text
    
def process_article(article, ticker, news_instance, reference_date):
    
    if article['date'] >= reference_date:
        try:
            article['ticker'] = ticker
            text = news_instance.get_full_article(article['url'])
            article['summary'] = news_instance.openai(f"Notícia sobre {ticker}: {text}")
            pattern = r"A nota é:\s*(-?\d+)"
            match = re.search(pattern, article['summary'])
            article['score'] = match.group(1) if match else None
            
            items = {'ticker', 'date', 'url', 'summary', 'score'}
            return {k: v for k, v in article.items() if k in items}
        
        except Exception as e:
            print(f"Error processing article for {ticker}: {e}")
            return
        
    
def main():
    
    df_tickers = Database('stock_data', Config.DATABASE).view()
    tickers_list = np.array(df_tickers['ticker'].unique())

    d_7 =  str(datetime.today() - timedelta(days=7))
    data = []
    
    for ticker in tqdm(tickers_list, desc='Processing tickers'):
        news = News(ticker)
        
        response = news.get_news()

        if response:
            for article in response:
                processed_article = process_article(article, ticker, news, d_7)
                
                if processed_article:
                    data.append(processed_article)

    df_article = pd.DataFrame(data)
    return df_article

if __name__ == "__main__":
    main()
