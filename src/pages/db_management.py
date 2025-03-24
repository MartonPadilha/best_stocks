import streamlit as st
import pandas as pd
from webscraping import main as webscraping
from database import Database
from config import Config

db = Database('stock_data', Config.DATABASE)

st.set_page_config(layout='wide')

st.title('Gerenciamento do Banco de Dados')

choose_option = st.radio('O que deseja fazer?', ['Visualizar Dados', 'Atualizar Dados'])
st.text(f"Database: {Config.DATABASE}\nTabela: stock_data")

if choose_option == 'Visualizar Dados':
    df = db.view()
    if df is None:
        st.text("Sem dados!")
    else:
        st.dataframe(df)
        
elif choose_option == 'Atualizar Dados':
    st.subheader("Atualizar Dados do Banco")
    st.text("Atualizar o banco de dados apagará todos os dados atuais e adicionará os mais recentes.")
    if st.button("Confirmar Atualização"):
        with st.spinner("Atualizando os dados... Isso pode demarar alguns minutos."):
            df = webscraping()
            db.append(df, ['ticker', 'reference_date'])
            st.success("Dados atualizados com sucesso!")
    