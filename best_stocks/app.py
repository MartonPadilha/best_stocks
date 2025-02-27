import pandas as pd
import numpy as np
import streamlit as st
from fetch_data import main as api_data_main
from config import Config
from analysis import Calcs
import warnings


warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=pd.errors.SettingWithCopyWarning)

# Definindo os pesos padrão
default_weights = Config.WEIGHTS_STOCKS
calcs = Calcs(default_weights)

def update_analysis(weights):
    df_base = api_data_main()
    df_base['number_code'] = df_base['ticker'].astype(str).str.strip().str.extract(r'(\d+)(?!.*\d)')
    df_base['number_code'] = df_base['number_code'].astype(float).astype('Int64')

    if weights == Config.WEIGHTS_STOCKS:
        type_filter = Config.STOCK_SUFIX
    if weights == Config.WEIGHTS_FIIS:
        type_filter = Config.FII_SUFIX

    df_base = df_base[df_base['number_code'].isin(type_filter)]
    
    df = calcs.outliers_zscore(df_base, 3)

    df_sectorized = calcs.sector_analyses(df)
    df_general = calcs.general_analyses(df)

    df_final = calcs.final_sum_score(df_sectorized, df_general)
    df_final = df_final.sort_values(by=['score_final'], ascending=False)

    df_final = pd.merge(df_final, df_base, on='ticker', how='inner')

    return df_final

st.set_page_config(layout="wide")

# Criando a interface com Streamlit
st.title('Análise de Ações e FIIs')

# Ajuste interativo dos pesos dos indicadores
st.sidebar.header('Ajuste os Pesos dos Indicadores')

for i in Config.WEIGHTS_STOCKS.keys():
    value = st.sidebar.number_input(i, 0.0, 1.0, 0.0, 0.01)
    Config.WEIGHTS_STOCKS[i]['weight'] = value


apply_button = st.sidebar.button('Aplicar Filtros')

# sum_weights = np.sum(np.array([i for i in Config.WEIGHTS_STOCKS.values()]))
# st.sidebar.text(f"Soma dos pesos: {sum_weights}")

if apply_button:
    df_final = update_analysis(Config.WEIGHTS_STOCKS)

    # Exibe o resultado
    st.write('Ações rankeadas:')
    
    st.dataframe(df_final, use_container_width=True)
