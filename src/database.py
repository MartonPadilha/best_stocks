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
            
    def _connect(self):
        return sqlite3.connect(self.db_path)

    def get_history(self, data_type):
        """
        Retorna o histórico 'long' para o tipo (stock / fii).
        Assume que na tabela (ex: stock_data) existem múltiplos registros por ticker ao longo do tempo,
        com coluna 'reference_date' ou 'date' que seja interpretável como datetime.
        """
        table = 'stock_data' if data_type == 'stock' else 'fii_data'
        try:
            conn = self._connect()
            df = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=['reference_date'], index_col=None)
            conn.close()
            # normalizações mínimas de nomes de coluna:
            if 'reference_date' in df.columns:
                df = df.rename(columns={'reference_date': 'date'})
            # garantir colunas essenciais (preenchidas com NaN se não existirem)
            expected = ['ticker','date','price','p_l','p_vp','dy','m_líquida','roe','roic',
                        'liq_corrente','dív_líquida_ebitda','lucro_liquido','ebitda','receita','sector']
            for c in expected:
                if c not in df.columns:
                    df[c] = pd.NA
            # manter índice simples
            df = df.reset_index(drop=True)
            return df
        except Exception as e:
            logging.error("Erro get_history: %s", e)
            return pd.DataFrame()

    def get_snapshot(self, data_type):
        """
        Retorna um snapshot 'mais recente' por ticker. Usa a tabela mesma (agrupa por ticker pegando a última date).
        Útil para juntar metadados fixos (sector, type) com as features rolling.
        """
        table = 'stock_data' if data_type == 'stock' else 'fii_data'
        try:
            conn = self._connect()
            df = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=['reference_date'], index_col=None)
            conn.close()
            if 'reference_date' in df.columns:
                df = df.rename(columns={'reference_date': 'date'})
            # pegar último registro por ticker
            df = df.sort_values(['ticker', 'date']).groupby('ticker').tail(1).reset_index(drop=True)
            # renomear colunas para padrão usado no pipeline se necessário
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'reference_date'})
            return df
        except Exception as e:
            logging.error("Erro get_snapshot: %s", e)
            return pd.DataFrame()