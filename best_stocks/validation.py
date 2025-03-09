import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from database import Database
from config import Config
import ast
import yfinance as yf

# key = '2dc837788fa646428797caa6570f4a9b'

# def obter_noticias(ticker, api_key='sua_api_key'):
#     url = f'https://newsapi.org/v2/everything?q={ticker}&apiKey={api_key}'
#     response = requests.get(url)
#     dados = response.json()
    
#     noticias = []
#     for artigo in dados['articles']:
#         noticia = {
#             'titulo': artigo['title'],
#             'descricao': artigo['description'],
#             'data': artigo['publishedAt'],
#             'url': artigo['url']
#         }
#         noticias.append(noticia)
    
#     return noticias

# print(obter_noticias('LAVV3', key)[1]['descricao'])

# def obter_texto_completo(url):
#     headers = {'User-Agent': 'Mozilla/5.0'}
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Tente encontrar o corpo do artigo (isso varia de site para site)
#         paragrafos = soup.find_all('p')
#         texto_completo = ' '.join([p.get_text() for p in paragrafos])
        
#         return texto_completo
#     else:
#         return "Não foi possível obter a notícia."

# # Testando com uma URL da Suno
# url = "https://www.suno.com.br/noticias/petrobras-petr4-dividendos-robustos-btg-4t24-gss/"
# print(obter_texto_completo(url))