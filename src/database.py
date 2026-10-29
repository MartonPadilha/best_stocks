import sqlite3
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, table_name, db_path):
        self.table_name = table_name
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def view(self):
        logger.info("Visualização da tabela %s", self.table_name)
        try:
            conn = self._connect()
            df = pd.read_sql(f"SELECT * FROM {self.table_name}", conn)
            conn.close()
        except Exception as e:
            logger.error("%s %s", 30 * "=", e)
            df = None
        return df

    def create(self, df):
        logger.info("Criando e salvando os dados na tabela %s", self.table_name)
        try:
            conn = self._connect()
            df.to_sql(self.table_name, conn, if_exists="replace", index=False)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Erro ao salvar os dados: %s", e)

    def append(self, data, key):
        try:
            conn = self._connect()
            key_expr = " || '|' || ".join(key)
            query = f"SELECT {key_expr} AS key FROM {self.table_name}"
            existing_keys = set(pd.read_sql(query, conn)["key"])
            data_key = data[key].astype(str).agg("|".join, axis=1)
            data_to_append = data[~data_key.isin(existing_keys)]
            if not data_to_append.empty:
                data_to_append.to_sql(self.table_name, conn, if_exists="append", index=False)
                conn.commit()
                logger.info("%s new records added with success!", len(data_to_append))
            else:
                logger.info("No records added!")
            conn.close()
        except Exception as e:
            logger.error("Error: %s", e)

    def delete(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            conn.commit()
            conn.close()
            logger.info("Tabela %s deletada com sucesso!", self.table_name)
        except Exception as e:
            logger.error("Erro ao deletar a tabela: %s", e)

    def table_exists(self) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (self.table_name,),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def _sql_type_for(series: pd.Series) -> str:
        dtype = series.dtype
        if pd.api.types.is_integer_dtype(dtype):
            return "INTEGER"
        if pd.api.types.is_float_dtype(dtype):
            return "REAL"
        if pd.api.types.is_bool_dtype(dtype):
            return "INTEGER"
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "TEXT"
        return "TEXT"

    def count_rows(self) -> int:
        if not self.table_exists():
            return 0
        conn = self._connect()
        try:
            cur = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            return cur.fetchone()[0]
        finally:
            conn.close()

    def append_if_new(self, df, keys) -> dict:
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            logger.info("append_if_new: DataFrame vazio para %s; nada a fazer.", self.table_name)
            return {"fetched_rows": 0, "inserted_rows": 0, "rejected_rows": 0, "skipped": True}

        missing = [c for c in keys if c not in df.columns]
        if missing:
            raise ValueError(f"Colunas de chave ausentes: {missing}")

        df = df.copy()
        df_keys = df[keys].astype(str).agg("|".join, axis=1)

        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            if self.table_exists():
                existing_cols = {row[1] for row in conn.execute(f"PRAGMA table_info({self.table_name})").fetchall()}
                for col in df.columns:
                    if col not in existing_cols:
                        sql_type = self._sql_type_for(df[col])
                        conn.execute(f"ALTER TABLE {self.table_name} ADD COLUMN {col} {sql_type}")
                        logger.info("Schema drift: adicionada coluna %s (%s) em %s", col, sql_type, self.table_name)
                key_expr = " || '|' || ".join(keys)
                existing = set(pd.read_sql(f"SELECT {key_expr} AS key FROM {self.table_name}", conn)["key"])
            else:
                existing = set()

            mask_new = ~df_keys.isin(existing)
            null_key_mask = df[keys].isnull().any(axis=1)
            mask_insert = mask_new & ~null_key_mask
            df_to_insert = df[mask_insert]

            inserted = 0
            if not df_to_insert.empty:
                df_to_insert.to_sql(self.table_name, conn, if_exists="append", index=False)
                inserted = len(df_to_insert)

            conn.commit()
            return {
                "fetched_rows": len(df),
                "inserted_rows": inserted,
                "rejected_rows": int(null_key_mask.sum()),
                "skipped": False,
            }
        except Exception as e:
            conn.rollback()
            logger.error("append_if_new falhou: %s", e)
            raise
        finally:
            conn.close()

    def replace_if_non_empty(self, df) -> dict:
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            logger.info("replace_if_non_empty: DataFrame vazio para %s; tabela preservada.", self.table_name)
            return {"fetched_rows": 0, "inserted_rows": 0, "rejected_rows": 0, "skipped": True}

        conn = self._connect()
        try:
            staging = f"{self.table_name}__staging"
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(f"DROP TABLE IF EXISTS {staging}")
            df.to_sql(staging, conn, if_exists="replace", index=False)
            staged_count = conn.execute(f"SELECT COUNT(*) FROM {staging}").fetchone()[0]
            if staged_count == 0:
                conn.rollback()
                return {"fetched_rows": len(df), "inserted_rows": 0, "rejected_rows": 0, "skipped": True}

            old_backup = f"{self.table_name}__old"
            conn.execute(f"DROP TABLE IF EXISTS {old_backup}")
            if self.table_exists():
                conn.execute(f"ALTER TABLE {self.table_name} RENAME TO {old_backup}")
            conn.execute(f"ALTER TABLE {staging} RENAME TO {self.table_name}")
            conn.execute(f"DROP TABLE IF EXISTS {old_backup}")
            conn.commit()
            return {
                "fetched_rows": len(df),
                "inserted_rows": staged_count,
                "rejected_rows": 0,
                "skipped": False,
            }
        except Exception as e:
            conn.rollback()
            logger.error("replace_if_non_empty falhou: %s", e)
            raise
        finally:
            conn.close()

    def get_history(self, data_type):
        table = "stock_data" if data_type == "stock" else "fii_data"
        try:
            conn = self._connect()
            df = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=["reference_date"], index_col=None)
            conn.close()
            if "reference_date" in df.columns:
                df = df.rename(columns={"reference_date": "date"})
            expected = [
                "ticker", "date", "price", "p_l", "p_vp", "dy", "m_líquida", "roe", "roic",
                "liq_corrente", "dív_líquida_ebitda", "lucro_liquido", "ebitda", "receita", "sector",
            ]
            for c in expected:
                if c not in df.columns:
                    df[c] = pd.NA
            return df.reset_index(drop=True)
        except Exception as e:
            logging.error("Erro get_history: %s", e)
            return pd.DataFrame()

    def get_snapshot(self, data_type):
        table = "stock_data" if data_type == "stock" else "fii_data"
        try:
            conn = self._connect()
            df = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=["reference_date"], index_col=None)
            conn.close()
            if "reference_date" in df.columns:
                df = df.rename(columns={"reference_date": "date"})
            df = df.sort_values(["ticker", "date"]).groupby("ticker").tail(1).reset_index(drop=True)
            if "date" in df.columns:
                df = df.rename(columns={"date": "reference_date"})
            return df
        except Exception as e:
            logging.error("Erro get_snapshot: %s", e)
            return pd.DataFrame()
