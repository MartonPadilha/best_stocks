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
            
    def append(self, data, key):
        try: 
            conn = sqlite3.connect(self.db_path)
            
            key_expr = " || ".join(key)
            
            query = f"SELECT {key_expr} AS key FROM {self.table_name}"

            existing_keys = set(pd.read_sql(query, conn)['key'])
            
            data['key'] = data[key].astype(str).agg(''.join, axis = 1)

            data_to_append = data[~data['key'].isin(existing_keys)].drop(columns=['key'])

            if not data_to_append.empty:
                data_to_append.to_sql(self.table_name, conn, if_exists="append", index=False)
                print(f'{len(data_to_append)} new records added with success!')
            else:
                print("No records added!")
        except Exception as e:
            print('Error:', e)
            return
            
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
            