import pandas as pd
import numpy as np
import streamlit as st
from database import Database
from config import Config
from analysis import Calcs
import warnings


warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)

db = Database('stock_data', Config.DATABASE)

def update_analysis(weights, type):
    df_base = db.view()
    df_base = df_base[df_base['type'] == type]
    
    df, outliers = calcs.outliers_zscore(df_base, 3)

    df_sectorized = calcs.sector_analyses(df)
    df_general = calcs.general_analyses(df)

    df_final = calcs.final_sum_score(df_sectorized, df_general)
    df_final = df_final.sort_values(by=['score_final'], ascending=False)

    df_final = pd.merge(df_final, df_base, on='ticker', how='inner')

    return df_final, outliers

st.set_page_config(layout='wide')

##################### HEADER #########################
choose_buttom = st.radio('Selecione o tipo de investimento:', ['Ações', 'FIIs'])

if choose_buttom == "Ações":
    _type = 'stock'
    choose_weight = Config.WEIGHTS_STOCKS
    calcs = Calcs(choose_weight)
    st.header(f'Análise de {choose_buttom}')
    st.write(f'Você pode visualizar e analisar {choose_buttom} com base nos indicadores e pesos escolhidos.')
    # st.line_chart({"Preço": [100, 105, 102, 110, 108]})
elif choose_buttom == "FIIs":
    choose_weight = Config.WEIGHTS_FIIS
    calcs = Calcs(choose_weight)
    st.header(f'Análise de {choose_buttom}')
    st.write(f'Você pode visualizar e analisar {choose_buttom} com base nos indicadores e pesos escolhidos.')
    # st.line_chart({"Preço": [100, 105, 102, 110, 108]})
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
    df_final, outliers = update_analysis(choose_weight, _type)

    st.write('Ações rankeadas:')
    st.dataframe(df_final)
    
    st.write('Outliers:')
    st.dataframe(outliers)
######################################################



