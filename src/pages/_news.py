import streamlit as st
import pandas as pd
from src.database import Database
from src.config import Config
import numpy as np
from src.news import News
import re
from datetime import datetime, timedelta

df_tickers = Database('stock_data', Config.DATABASE).view()
tickers_list = np.array(df_tickers['ticker'])
# st.set_page_config(layout='wide')
db_news = Database('news', Config.DATABASE)

def add_data():
    d_7 =  str(datetime.today() - timedelta(days=7))
    data = []
    for ticker in tickers_list:

        news = News(ticker)

        response = news.get_news()

        if response:
            for article in response:
                if article['date'] >= d_7:
                    print(f'Novas notícias para {ticker}')
                    try:
                        article['ticker'] = ticker
                        text = news.get_full_article(article['url'])
                        article['summary'] = news.openai(f"Noticia sobre {ticker}: {text}")
                        pattern = r"A nota é:\s*(-?\d+)"
                        match = re.search(pattern, article['summary'])
                        article['score'] = match.group(1) if match else None

                        itens = {'ticker', 'date', 'url', 'summary', 'score'}
                        article = {k: [v] for k, v in article.items() if k in itens }
                        data.append(article)

                    except Exception as e:
                        print(ticker, e)
        
    df_article = pd.DataFrame(data)

    db_news.append(df_article, ['url'])


df = db_news.view()
df['score'] = df['score'].astype(float)
df['avg_score'] = df.groupby('ticker')['score'].transform('mean')

filtro = st.text_input("Filtrar por empresa:")


if filtro is None:
    st.dataframe(df)
else:
    st.dataframe(df[df['ticker'].str.contains(filtro, case = False, na=False)])
    
add_data()
