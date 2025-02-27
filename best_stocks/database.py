import sqlite3
import pandas as pd
import logging

class Database():
    def __init__(self, table_name, db_path):
        self.table_name = table_name
        self.db_path = db_path
        # self.conn = sqlite3.connect(conn)
        
    def view(self):
        print(f'Visualização da tabela {self.table_name}...')
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql(f"SELECT * FROM {self.table_name}", conn)
            conn.close()
        except Exception as e:
            print(30*'=', e)
            df = None
            
        return df

    def create(self, df):
        print("Criando e salvando os dados...")
        try:
            conn = sqlite3.connect(self.db_path)
            df.to_sql(self.table_name, conn, if_exists="replace", index=False)
            conn.close()
        except Exception as e:
            print("Erro ao salvar os dados:", e)