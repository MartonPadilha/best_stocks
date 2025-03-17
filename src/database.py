import sqlite3
import pandas as pd
import logging

class Database():
    def __init__(self, table_name, db_path):
        self.table_name = table_name
        self.db_path = db_path
        
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
            
    def append(self, data):
        try: 
            conn = sqlite3.connect(self.db_path)
            data.to_sql(self.table_name, conn, if_exists="append", index=False)
            conn.close()
            print(f'Dados adicionados com sucesso!')
        except Exception as e:
            print('Erro ao adicionar dados:', e)
            
    def delete(self):
        try: 
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f'DROP TABLE IF EXISTS {self.table_name}')
            conn.commit()
            conn.close()
            print(f'Tabela {self.table_name} deletada com sucesso!')
        except Exception as e:
            print('Erro ao deletar a tabela:', e)