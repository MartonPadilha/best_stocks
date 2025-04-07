import pandas as pd
import numpy as np
from config import Config
import logging
import matplotlib.pyplot as plt
from scipy.stats import zscore
import time


class Calcs():
    def __init__(self, goal):
        self.goal = goal
        
    def outliers_iqr(self, df, factor=1.5):
        """
        Get outliers using interquartile range method (IQR).

        Args:
            df (pd.DataFrame): DataFrame with the data to analyses.
            factor (float, optional): Multiplicative factor to set limits. Default is 1.5. 

        Returns:
            tuple: DataFrame without outliers, DataFrame with only outliers.
        """
        df['outlier'] = False
        
        for metric_col in [i for i in self.goal.keys()]:
            metric_array = np.array(df[df[metric_col] != 0][metric_col].dropna())

            first_quartil = np.percentile(metric_array, 25)
            third_quartil = np.percentile(metric_array, 75)
            iqr = third_quartil - first_quartil
            
            lower_limit = first_quartil - factor * iqr
            upper_limit = third_quartil + factor * iqr
            
            df.loc[(df[metric_col] < lower_limit) | (df[metric_col] > upper_limit), 'outlier'] = True
            
        return df[df['outlier'] == False], df[df['outlier'] == True]
    
    def outliers_zscore(self, df, factor=3):
        """
        Get outliers using zscore method.

        Args:
            df (pd.DataFrame): DataFrame with the data to analyses.
            factor (float, optional): Factor limit to consirer the data an outlier. Default is 3. 

        Returns:
            tuple: DataFrame without outliers, DataFrame with only outliers.
        """
        df['outlier'] = False
        
        for metric_col in [i for i in self.goal.keys()]:
            
            df.loc[np.abs(zscore(df[metric_col].dropna())) > factor, 'outlier'] = True
            
        return df[df['outlier'] == False], df[df['outlier'] == True]

    def normalize(self, df, cols):
        """
        Data normalization using MinMax under different conditionals.

        Args:
            df (pd.DataFrame): DataFrame with data.
            cols (list): Columns list to normalize.

        Returns:
            pd.DataFrame: DataFrame normalized.
        """
        
        for col in cols:
            if self.goal[col]['normalization'] == 'inverter':
                _min, _max = df[col].min(), df[col].max()
                df.loc[:, col] = (df[col] - _min) / (_max - _min)
                df.loc[:, col] = 1 - df[col]
                
            elif self.goal[col]['normalization'] == 'inverter_zero':
                # df[col] = np.log1p(df[col]) # I chose a logarithmic scale to smooth out de high variance of the values
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
                                   
            # treat NaN
            df[col] = df[col].fillna(0)
            
        return df

    def sum_score(self, df):
        """
        Calculates the weighted total score based on criteria.
        
        Args:
            df (pd.DataFrame): DataFrame with data.

        Returns:
            float: Score calculated.
        """
        
        score = 0
        
        for crit, weight in self.goal.items():
            score += df[crit] * weight['weight']

        return score

    def final_sum_score(self, df_sector, df_general):
        """
        Calculates the weighted total score joining sector and general scores.
        
        Args:
            df_sector (pd.DataFrame): DataFrame with sector score.
            df_general (pd.DataFrame): DataFrame with general score.

        Returns:
            float: Final score calculated.
        """

        score = 0
        df_merge = pd.merge(df_sector, df_general, on='ticker', how='inner')

        for col, peso in Config.WEIGHTS_ANALYSIS.items():
            score += df_merge[col] * peso
            
        df_merge['score_final'] = score
            
        return df_merge[['ticker', 'score_sector', 'score_general', 'score_final']]

    
    def sector_analyses(self, df):
        """
        Calculates score based on indicators weight splited by sector.

        Args:
            df (pd.DataFrame): DataFrame with data.

        Returns:
            pd.DataFrame: DataFrame with sectorial score.
        """

        df_sectorized = pd.DataFrame(columns=df.columns)
        for sector in df['sector'].unique():
            df_sector = df[df['sector'] == sector]
            df_normalized = self.normalize(df_sector, [i for i in self.goal])
            df_normalized['score_sector'] = df_normalized.apply(self.sum_score, axis=1)
            df_sectorized = pd.concat([df_sectorized, df_normalized])
        
        return df_sectorized
            
    def general_analyses(self, df):
        """
        Calculates general score based on indicators weight.

        Args:
            df (pd.DataFrame): DataFrame with data.

        Returns:
            pd.DataFrame: DataFrame with general score.
        """

        df_normalized = self.normalize(df, [i for i in self.goal])
        df_normalized['score_general'] = df.apply(self.sum_score, axis=1)

        return df_normalized
