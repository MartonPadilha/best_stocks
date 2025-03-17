
import pandas as pd
import numpy as np
from fetch_data import main as api_data_main
from config import Config
from analysis import Calcs
import time

pd.options.mode.chained_assignment = None

GOAL = Config.WEIGHTS_STOCKS
calcs = Calcs(GOAL)

df_base = api_data_main()
# df_base = df_base[[]]

df_base['number_code'] = df_base['ticker'].astype(str).str.strip().str.extract(r'(\d+)(?!.*\d)')
df_base['number_code'] = df_base['number_code'].astype(float).astype('Int64')

if GOAL == Config.WEIGHTS_STOCKS:
    type_filter = Config.STOCK_SUFIX
if GOAL == Config.WEIGHTS_FIIS:
    type_filter = Config.FII_SUFIX

df_base = df_base[df_base['number_code'].isin(type_filter)]
df = calcs.outliers_zscore(df_base, 3)

df_sectorized = calcs.sector_analyses(df)
df_general = calcs.general_analyses(df)
print(df_general[df_general['ticker'] == 'SOJA3'][['div_liq_ebitda', 'liq_corrent', 'p_l', 'p_vp']])

df_final = calcs.final_sum_score(df_sectorized, df_general)

df_final = df_final.sort_values(by=['score_final'], ascending=False)

df_final = pd.merge(df_final, df_base, on='ticker', how='inner')
# print(df_final[df_final['sector'].isin(['Utilidade Pública'])])

print(df_final)

df_final.to_csv(f'output/data.csv', sep=';', encoding='utf-8', index=False, decimal=",")
