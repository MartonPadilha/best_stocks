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
    # calcs = Calcs(choose_weight)
    

    st.header(f'Análise de {choose_buttom}')
    st.write(f'Você pode visualizar e analisar {choose_buttom} com base nos indicadores e pesos escolhidos.')

elif choose_buttom == "FIIs":
    _type = 'fii'
    choose_weight = Config.WEIGHTS_FIIS
    # calcs = Calcs(choose_weight)
    st.header(f'Análise de {choose_buttom}')
    st.write(f'Você pode visualizar e analisar {choose_buttom} com base nos indicadores e pesos escolhidos.')

#####################################################

st.sidebar.markdown("---")
st.sidebar.header("Temporal & Robustez")
win_30 = st.sidebar.number_input("Janela curta (dias)", 7, 60, 30, step=1)
win_90 = st.sidebar.number_input("Janela média (dias)", 30, 180, 90, step=1)
win_180 = st.sidebar.number_input("Janela longa (dias)", 90, 365, 180, step=1)
winsor_lo = st.sidebar.slider("Winsorize lower quantile (%)", 0.0, 5.0, 1.0) / 100.0
winsor_hi = st.sidebar.slider("Winsorize upper quantile (%)", 95.0, 100.0, 99.0) / 100.0
calcs = Calcs(choose_weight, temporal_windows=[win_30, win_90, win_180], winsor_limits=(winsor_lo, winsor_hi))

################ SIDEBAR #############################
st.sidebar.header('Pesos dos indicadores')
sum_weights = np.sum(np.array([i['weight'] for i in choose_weight.values()]))
st.sidebar.text(f"Soma dos pesos: {sum_weights}")

for i in choose_weight:
    value = st.sidebar.number_input(i, 0.0, 1.0, choose_weight[i]['weight'], 0.01)
    choose_weight[i]['weight'] = value

# Botão "Aplicar filtros"
if st.sidebar.button('Aplicar Filtros'):
    st.session_state['filters_applied'] = True

######################################################


################ BODY ################################
if st.session_state.get('filters_applied', False):

    if _type == 'stock':
        st.subheader('Ações rankeadas:')
        st.dataframe(analysis_tickers(_type, calcs)[0])
        
        st.subheader('Dividendos:')
        st.dataframe(show_dividends())
        
        st.write('Notícias:')
        st.dataframe(show_news())
        
        st.write('Outliers:')
        st.dataframe(analysis_tickers(_type, calcs)[1])
        
        # === Seletor de período (novo) ===
        st.markdown("---")
        st.subheader("Gráfico de Rank das Top Ações")

        period_choice = st.radio(
            "Selecione o período de análise:",
            ('7 dias', '30 dias', '90 dias', '1 ano', 'Todas as datas'),
            horizontal=True,
            key='period_choice'
        )

        period_map = {
            '7 dias': '7d',
            '30 dias': '30d',
            '90 dias': '90d',
            '1 ano': '1y',
            'Todas as datas': 'all'
        }
        selected_period = period_map[period_choice]

        df_graph = analysis_rank(_type, calcs, period=selected_period)
        st.plotly_chart(plot_rank(df_graph, 'date', 'rank'), use_container_width=True)

    elif _type == 'fii':
        st.write("FIIs analysis is not implemented yet.")
        st.dataframe(show_fiis())

else:
    st.info("Ajuste os pesos e clique em **Aplicar Filtros** para iniciar a análise.")
######################################################
