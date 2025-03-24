import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import random
import openai
import re
import pandas as pd
from .database import Database

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
        except:
            return None
        
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
        import google.generativeai as genai
        
        prompt = f"""Em um paragrafo, avalie a notícia abaixo de acordo com sua qualidade geral e impacto positivo ou negativo no para a empresa no mercado financeiro, dê uma nota de -2 a 2, considerando:
                -2: A notícia é extremamente negativa e prejudicial, com um impacto sério e imediato para empresa ou mercado financeiro.
                -1: A notícia é negativa, mas com um impacto moderado ou de longo prazo, que pode gerar alguma preocupação para empresa ou mercado financeiro.
                0: A notícia é neutra, sem impacto significativo, positiva ou negativa.
                1: A notícia é positiva, com um impacto positivo e um benefício moderado para o mercado ou para a empresa.
                2: A notícia é extremamente positiva, com impacto muito favorável, podendo gerar grandes ganhos ou um grande impulso no mercado ou na empresa.

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