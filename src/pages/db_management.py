import streamlit as st
from database import Database
from config import Config
import importlib.util
import os

DB_PATH = Config.DATABASE
    
def load_and_run(table_name):
    file_path = Config.TABLES[table_name]['file']
    
    if not os.path.exists(file_path):
            raise FileNotFoundError(f"Erro: Arquivo '{file_path}' não encontrado.")
        
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    if hasattr(module, "main"):
        return module.main()
    else:
        raise AttributeError(f"Erro: O módulo '{module_name}' não tem uma função 'main'.")

st.title("Gerenciamento do Banco de Dados SQLite")

tables = Config.TABLES.keys()

if not tables:
    st.warning("Nenhuma tabela encontrada no banco de dados.")
    st.stop()
    
selected_table = st.selectbox("Escolha uma tabela:", tables)

db = Database(selected_table, DB_PATH)

st.subheader(f"Dados da tabela: {selected_table}")
df = db.view()
if df is not None and not df.empty:
    st.dataframe(df)
else:
    st.write("Tabela vazia ou erro ao carregar dados.")
    
st.subheader(f"Atualizar dados da tabela: {selected_table}")

insert_mode = Config.TABLES[selected_table]['insert']
st.text(f"Método de atualização dessa tabela: {insert_mode.upper()}")

if st.button("Atualizar Tabela"):
    with st.spinner("Atualizando dados..."):
        try:
            df = load_and_run(selected_table)
            
            if insert_mode == 'overwrite':
                db.create(df)
            elif insert_mode == 'append':
                db.append(df, Config.TABLES[selected_table]['keys'])
                
            st.write('Dados Atualizados.')
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar a tabela {selected_table}: {e}")

