import pandas as pd
import numpy as np
from config import Config
import logging
import matplotlib.pyplot as plt
from scipy.stats import zscore
import time


class Calcs():
    def __init__(self, goal):
        # if goal == 'stock':
        #     self.goal = Config.WEIGHTS_STOCKS
        # elif goal == 'fii':
        #     self.goal = Config.WEIGHTS_FIIS
            
        self.goal = goal
        
    def outliers_iqr(self, df, factor=1.5):
        df['outlier'] = False
        
        for metric_col in [i for i in self.goal.keys()]:
            metric_array = np.array(df[df[metric_col] != 0][metric_col].dropna())

            first_quartil = np.percentile(metric_array, 25)
            third_quartil = np.percentile(metric_array, 75)
            iqr = third_quartil - first_quartil
            
            lower_limit = first_quartil - factor * iqr
            upper_limit = third_quartil + factor * iqr
            print(f'{metric_col}: {lower_limit} - {upper_limit}')
            
            df.loc[(df[metric_col] < lower_limit) | (df[metric_col] > upper_limit), 'outlier'] = True
            
        df[df['outlier'] == True].to_csv(f'output/outliers.csv', sep=';', encoding='utf-8', index=False, decimal=",") 
            
            
        return df[df['outlier'] == False]
    
    def outliers_zscore(self, df, factor=3):
        df['outlier'] = False
        
        for metric_col in [i for i in self.goal.keys()]:
            
            df.loc[np.abs(zscore(df[metric_col].dropna())) > factor, 'outlier'] = True
            
        df[df['outlier'] == True].to_csv(f'output/outliers.csv', sep=';', encoding='utf-8', index=False, decimal=",") 

        return df[df['outlier'] == False]

    def normalize(self, df, colunas):
        
        for col in colunas:
            if self.goal[col]['normalization'] == 'inverter':
                _min, _max = df[col].min(), df[col].max()
                df.loc[:, col] = (df[col] - _min) / (_max - _min)
                df.loc[:, col] = 1 - df[col]
                
            elif self.goal[col]['normalization'] == 'inverter_zero':
                df[col] = np.log1p(df[col]) # escolhi usar escala logaritmica para suavizar a alta amplitude dos dados
                _min, _max = df[col].min(), df[col].max()
                df.loc[df[col] <= 0, col] = np.nan
                df.loc[:, col] = (df[col] - _min) / (_max - _min)
                df.loc[:, col] = 1 - df[col]
                
            elif self.goal[col]['normalization'] == 'inverter_one':
                df.loc[:, col] = abs(df[col] - 1)
                _min, _max = df[col].min(), df[col].max()
                df.loc[:, col] = (df[col] - _min) / (_max - _min)
                df.loc[:, col] = 1 - df[col]
            else:
                _min, _max = df[col].min(), df[col].max()
                df.loc[:, col] = (df[col] - _min) / (_max - _min)
                                   
            #aqui resolvo os NaN
            df[col] = df[col].fillna(0)
            
        return df

    def sum_score(self, df):
        
        score = 0
        
        for crit, peso in self.goal.items():
            score += df[crit] * peso['weight']

        return score

    def final_sum_score(self, df_sector, df_general):
        #essa função pondera o score por setor e geral pelos pesos escolhidos e dps faz a soma de ambos.
        score = 0
        df_merge = pd.merge(df_sector, df_general, on='ticker', how='inner')

        for col, peso in Config.WEIGHTS_ANALYSIS.items():
            score += df_merge[col] * peso
            
        df_merge['score_final'] = score
            
        return df_merge[['ticker', 'score_sector', 'score_general', 'score_final']]

    
    def sector_analyses(self, df):
        print(20*'=', 'SECTOR', 20*'=')
        df_sectorized = pd.DataFrame(columns=df.columns)
        for sector in df['sector'].unique():
            df_sector = df[df['sector'] == sector]
            df_normalized = self.normalize(df_sector, [i for i in self.goal])
            df_normalized['score_sector'] = df_normalized.apply(self.sum_score, axis=1)
            df_sectorized = pd.concat([df_sectorized, df_normalized])
        
        return df_sectorized
            
    def general_analyses(self, df):
        print(20*'=', 'GENERAL', 20*'=')
        df_normalized = self.normalize(df, [i for i in self.goal])
        df_normalized['score_general'] = df.apply(self.sum_score, axis=1)

        return df_normalized
