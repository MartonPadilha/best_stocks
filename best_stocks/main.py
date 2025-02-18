
import pandas as pd
import numpy as np
from fetch_data import main as api_data_main
from config import Config
from analysis import Calcs
import time

pd.options.mode.chained_assignment = None

GOAL = 'fii'
calcs = Calcs(GOAL)

df_base = api_data_main()
df_base['number_code'] = df_base['ticker'].astype(str).str.strip().str.extract(r'(\d+)(?!.*\d)')
df_base['number_code'] = df_base['number_code'].astype(float).astype('Int64')

if GOAL == 'stock':
    type_filter = Config.STOCK_SUFIX
if GOAL == 'fii':
    type_filter = Config.FII_SUFIX

df_base = df_base[df_base['number_code'].isin(type_filter)]

df = calcs.outliers_iqr(df_base, 1.7)

df_sectorized = calcs.sector_analyses(df)
df_general = calcs.general_analyses(df)

df_final = calcs.final_sum_score(df_sectorized, df_general)

df_final = df_final.sort_values(by=['score_final'], ascending=False)

df_final = pd.merge(df_final, df_base, on='ticker', how='inner')

print(df_final[df_final['ticker'].isin(['CSED3', 'DIRR3'])])
print(df_final)

# df_sectorized.to_csv(f'output/{GOAL}_{time.time()}.csv', sep=';', encoding='utf-8', index=False, decimal=",")
