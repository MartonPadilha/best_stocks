import sqlite3
import pandas as pd
import logging

class Database():
    def __init__(self, table_name, conn):
        self.table_name = table_name
        self.conn = sqlite3.connect(conn)
        
    def view(self):
        logging.info(f'Visualização da tabela {self.table_name}...')
        try:
            df = pd.read_sql(f"SELECT * FROM {self.table_name}", self.conn)
        except:
            df = None
            
        return df

    def create(self, df):
        logging.info("Criando e salvando os dados...")
        df.to_sql(self.table_name, self.conn, if_exists="replace", index=False)

        return