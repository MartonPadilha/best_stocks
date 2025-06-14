import pandas as pd
import numpy as np
import streamlit as st
from database import Database
from config import Config
from analysis import Calcs
import warnings
import os
import sys

import sys
import os

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.append(src_path)

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)


def analysis_tickers(type):
    df_base = Database('stock_data', Config.DATABASE).view()
    
    max_date = df_base['reference_date'].max()
    df_base = df_base[df_base['reference_date'] == max_date]
    df_base = df_base[df_base['type'] == type]
    
    df, outliers = calcs.outliers_zscore(df_base, 4.5)

    df_sectorized = calcs.sector_analyses(df)
    df_general = calcs.general_analyses(df)

    df_final = calcs.final_sum_score(df_sectorized, df_general)
    df_final = df_final.sort_values(by=['score_final'], ascending=False)

    df_final = pd.merge(df_final, df_base, on='ticker', how='inner')

    return df_final, outliers

def analysis_rank(type):
    df_base = Database('stock_data', Config.DATABASE).view()
    
    df_base = df_base[df_base['type'] == type]
    
    unique_dates = df_base['reference_date'].sort_values().unique()
    
    result = []
    for date in unique_dates:
        df_day = df_base[df_base['reference_date'] == date]
        
        df, outliers = calcs.outliers_zscore(df_day, 4)

        df_sectorized = calcs.sector_analyses(df)
        df_general = calcs.general_analyses(df)

        df_final = calcs.final_sum_score(df_sectorized, df_general)
        df_final = df_final.sort_values(by=['score_final'], ascending=False)
        
        df_final['rank'] = df_final['score_final'].rank(ascending=False, method='min').astype(int)
        df_final['date'] = date
        result.append(df_final)
        
    df_all = pd.concat(result, ignore_index=True)

    return df_all[['date', 'ticker', 'rank']]

def show_dividends():
    df_base = Database('dividends', Config.DATABASE).view()
    
    df_base['total_value'] = df_base.groupby('ticker')['value'].transform('sum')

    return df_base

def show_news():
    df_base = Database('news', Config.DATABASE).view()
    df_base = df_base[df_base['score'].notnull()]
    df_base['score'] = df_base['score'].astype(int)
    df_base['avg_score'] = df_base.groupby('ticker')['score'].transform('mean')

    return df_base

st.set_page_config(layout='wide')

##################### HEADER #########################
choose_buttom = st.radio('Selecione o tipo de investimento:', ['Ações', 'FIIs'])

if choose_buttom == "Ações":
    _type = 'stock'
    choose_weight = Config.WEIGHTS_STOCKS
    calcs = Calcs(choose_weight)
    st.header(f'Análise de {choose_buttom}')
    st.write(f'Você pode visualizar e analisar {choose_buttom} com base nos indicadores e pesos escolhidos.')

elif choose_buttom == "FIIs":
    _type = 'fii'
    choose_weight = Config.WEIGHTS_FIIS
    calcs = Calcs(choose_weight)
    st.header(f'Análise de {choose_buttom}')
    st.write(f'Você pode visualizar e analisar {choose_buttom} com base nos indicadores e pesos escolhidos.')

#####################################################

################ SIDEBAR #############################
st.sidebar.header('Pesos dos indicadores')
sum_weights = np.sum(np.array([i['weight'] for i in choose_weight.values()]))
st.sidebar.text(f"Soma dos pesos: {sum_weights}")

for i in choose_weight:
    value = st.sidebar.number_input(i, 0.0, 1.0, choose_weight[i]['weight'], 0.01)
    choose_weight[i]['weight'] = value

apply_button = st.sidebar.button('Aplicar Filtros')
######################################################

      
################ BODY ################################
if apply_button:
    # df_final, outliers = analysis_tickers(_type)
    if _type == 'stock':

        st.subheader('Ações rankeadas:')
        st.dataframe(analysis_tickers(_type)[0])
        
        st.subheader('Dividendos:')
        st.dataframe(show_dividends())
        
        st.write('Notícias:')
        st.dataframe(show_news())
        
        st.write('Outliers:')
        st.dataframe(analysis_tickers(_type)[1])
        
        ### Line Graph - Rank top tickers
        df_graph = analysis_rank(_type)
        filter_ = df_graph.groupby('ticker')['rank'].mean().reset_index()
        filter_['rank'] = filter_['rank'].rank(ascending=True).astype(int)
        top_tickers = np.array(filter_[filter_['rank'] <= 10]['ticker'])

        df_filtered = df_graph[df_graph['ticker'].isin(top_tickers)]
        import plotly.express as px
        fig = px.line(
            df_filtered,
            x='date',
            y='rank',
            color='ticker',
            title='Evolução do Rank por Ticker',
            markers=True
        )
        fig.update_yaxes(autorange='reversed')

        st.plotly_chart(fig, use_container_width=True)

    elif _type == 'fii':
        st.write("FIIs analysis is not implemented yet.")
    
######################################################
