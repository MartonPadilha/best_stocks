import pandas as pd
import numpy as np
import streamlit as st
from database import Database
from config import Config
from analysis import Calcs
from stock_app import *
from fii_app import *
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
    if _type == 'stock':
        print(calcs)
        st.subheader('Ações rankeadas:')
        st.dataframe(analysis_tickers(_type, calcs)[0])
        
        st.subheader('Dividendos:')
        st.dataframe(show_dividends())
        
        st.write('Notícias:')
        st.dataframe(show_news())
        
        st.write('Outliers:')
        st.dataframe(analysis_tickers(_type, calcs)[1])
        
        ### Line Graph - Rank top tickers
        df_graph = analysis_rank(_type, calcs)

        st.plotly_chart(plot_rank(df_graph, 'date', 'rank'), use_container_width=True)

    elif _type == 'fii':
        st.write("FIIs analysis is not implemented yet.")
        st.dataframe(show_fiis())
    
######################################################
