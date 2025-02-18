
import pandas as pd
import numpy as np
from best_stocks.fetch_data import main as api_data_main
from best_stocks.config import Config
from best_stocks.analysis import Calcs
import time

pd.options.mode.chained_assignment = None

GOAL = 'stock'
calcs = Calcs(GOAL)

df_base = api_data_main()
df_base['number_code'] = df_base['ticker'].astype(str).str.strip().str.extract(r'(\d+)(?!.*\d)')
df_base['number_code'] = df_base['number_code'].astype(float).astype('Int64')

if GOAL == 'stock':
    type_filter = Config.STOCK_SUFIX
if GOAL == 'fii':
    type_filter = Config.FII_SUFIX

df_base = df_base[df_base['number_code'].isin(type_filter)]

df = calcs.outliers_iqr(df_base, 1.5)

df_sectorized = calcs.sector_analyses(df)
df_general = calcs.general_analyses(df)

df_final = calcs.final_sum_score(df_sectorized, df_general)

df_final = df_final.sort_values(by=['score_final'], ascending=False)

df_final = pd.merge(df_final, df_base, on='ticker', how='inner')
# print(df_base[df_base['ticker'] == 'STBP3'])
# print(df_final)
print('df_base', df_base[df_base['ticker'] == 'PINE3'])
print('df_sectorized', df_sectorized[df_sectorized['ticker'] == 'PINE3'])
# print(df_general[df_general['ticker'] == 'PINE3'])
print('df_general', df_general[df_general['ticker'] == 'PINE3'])

# df_sectorized.to_csv(f'output/{GOAL}_{time.time()}.csv', sep=';', encoding='utf-8', index=False, decimal=",")
