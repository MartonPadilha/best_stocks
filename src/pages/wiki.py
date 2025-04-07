import streamlit as st

st.set_page_config(layout='wide')
st.title("Wiki do Projeto")

# Caminho do arquivo
file_path = "docs\wiki.txt"

# Ler o arquivo
with open(file_path, "r", encoding="utf-8") as file:
    content = file.read()

# Exibir no Streamlit
st.text_area("", content, height=1080)
