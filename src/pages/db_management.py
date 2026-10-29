import streamlit as st
from database import Database
from config import Config
from ingestion import run_ingestion

st.title("Gerenciamento do Banco de Dados SQLite")

tables = list(Config.TABLES.keys())

if not tables:
    st.warning("Nenhuma tabela encontrada no banco de dados.")
    st.stop()

selected_table = st.selectbox("Escolha uma tabela:", tables)

db = Database(selected_table, Config.DATABASE)

st.subheader(f"Dados da tabela: {selected_table}")
df = db.view()
if df is not None and not df.empty:
    st.dataframe(df)
else:
    st.write("Tabela vazia ou erro ao carregar dados.")

st.subheader(f"Atualizar dados da tabela: {selected_table}")

insert_mode = Config.TABLES[selected_table]["insert"]
st.text(f"Método de atualização dessa tabela: {insert_mode.upper()}")

if st.button("Atualizar Tabela"):
    with st.spinner("Atualizando dados..."):
        try:
            summary = run_ingestion(targets=[selected_table])
            res = summary["results"].get(selected_table, {})
            status = res.get("status")
            if summary["failed"] or status == "failed":
                st.error(f"Erro ao atualizar {selected_table}: {res.get('error', 'falha desconhecida')}")
            elif status == "skipped" and res.get("skipped"):
                st.info(f"Nenhum dado novo para {selected_table} (DataFrame vazio — tabela preservada).")
            else:
                st.success(
                    f"Dados atualizados: {res.get('inserted_rows', 0)} inseridos, "
                    f"{res.get('rejected_rows', 0)} rejeitados, "
                    f"{res.get('fetched_rows', 0)} coletados."
                )
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar a tabela {selected_table}: {e}")
