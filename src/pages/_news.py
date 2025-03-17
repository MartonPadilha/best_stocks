import streamlit as st
import pandas as pd
# from webscraping import main as webscraping
from ..database import Database
from ..config import Config
import numpy as np
from ..news import News
import re


df_tickers = Database('stock_data', Config.DATABASE).view()
tickers_list = np.array(df_tickers['ticker'])

db_news = Database('news', Config.DATABASE)
urls_list = np.array(db_news.view()['url'])

data = []
for ticker in tickers_list:

    news = News(ticker)

    response = news.get_news()

    if response:
        for article in response:
            if article['url'] not in urls_list:
                try:
                    article['ticker'] = ticker
                    text = news.get_full_article(article['url'])
                    article['summary'] = news.openai(f"Noticia sobre {ticker}: {text}")
                    pattern = r"A nota é:\s*(-?\d+)"
                    match = re.search(pattern, article['summary'])
                    article['score'] = match.group(1) if match else None

                    itens = {'ticker', 'date', 'url', 'summary', 'score'}
                    article = {k: [v] for k, v in article.items() if k in itens }

                    df_article = pd.DataFrame(article)
                    db_news.append(df_article)
                except Exception as e:
                    print(ticker, e)

print(db_news.view())