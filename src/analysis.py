import pandas as pd
import numpy as np
from config import Config
import logging
import matplotlib.pyplot as plt
from scipy.stats import zscore
import time


class Calcs():
    def __init__(self, goal, temporal_windows=None, winsor_limits=(0.01, 0.99)):
        self.goal = goal
        self.temporal_windows = temporal_windows or [30, 90, 180]
        self.winsor_limits = winsor_limits

    def add_rolling_features(self, df_history, price_col='price', date_col='date', ticker_col='ticker'):
        """
        df_history: dataframe long com colunas [ticker, date, price, p_l, p_vp, dy, m_liquida, roe, ...]
        Retorna df_latest com colunas rolling agregadas como p_l_90d_mean, dy_30d_mean, m_liq_180d_median, etc.
        """
        df = df_history.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values([ticker_col, date_col])
        out_rows = []

        agg_specs = {
            'p_l': ['mean', 'median'],
            'p_vp': ['mean'],
            'dy': ['mean'],
            'm_líquida': ['median'],
            'roe': ['median'],
            'roic': ['median'],
            'liq_corrente': ['median'],
            'dív_líquida_ebitda': ['median']
        }

        # loop por ticker e calcular rolling para cada janela
        for ticker, g in df.groupby(ticker_col):
            g = g.set_index(date_col).sort_index()
            row = {ticker_col: ticker, 'reference_date': g.index.max()}

            for win in self.temporal_windows:
                rolled = g.rolling(f"{win}D", min_periods=1)
                for col, aggs in agg_specs.items():
                    if col not in g.columns:
                        continue
                    for agg in aggs:
                        colname = f"{col}_{win}d_{agg}"
                        if agg == 'mean':
                            row[colname] = rolled[col].mean().iloc[-1]
                        elif agg == 'median':
                            row[colname] = rolled[col].median().iloc[-1]
            # LTM (últimos 4 trimestres) - assume col 'lucro' e 'ebitda' existam e tenham periodicidade trimestral,
            # mas se seu histórico diário tem colunas LTM calculadas, adapte.
            # Aqui vamos aproximar somando últimos ~365 dias:
            last_year = g.last('365D')
            for col in ['lucro_liquido', 'ebitda', 'receita']:
                if col in g.columns:
                    row[f"{col}_ltm"] = last_year[col].sum()
            # também calculo volatilidade preço
            if price_col in g.columns:
                row['price_std_90d'] = g['price'].rolling('90D', min_periods=5).std().iloc[-1]
                row['price_mean_90d'] = g['price'].rolling('90D', min_periods=5).mean().iloc[-1]
            out_rows.append(row)

        df_out = pd.DataFrame(out_rows)
        return df_out
    
    def winsorize_df(self, df, cols):
        lo_q, hi_q = self.winsor_limits
        df = df.copy()
        for c in cols:
            if c not in df.columns:
                continue
            lower = df[c].quantile(lo_q)
            upper = df[c].quantile(hi_q)
            df[c] = df[c].clip(lower, upper)
        return df
    
    def robust_normalize(self, df, cols, clip_q=(0.01, 0.99)):
        df = df.copy()
        for c in cols:
            if c not in df.columns:
                continue
            lo, hi = df[c].quantile(clip_q[0]), df[c].quantile(clip_q[1])
            s = df[c].copy()
            s = s.clip(lo, hi)
            # special handling for inverter types
            norm_type = self.goal.get(c, {}).get('normalization', 'default')
            if norm_type == 'inverter':
                # smaller is better
                s = (s - s.min()) / (s.max() - s.min())
                s = 1 - s
            elif norm_type == 'inverter_zero':
                # remove non-positive
                s = s.where(s > 0, np.nan)
                s = (s - s.min()) / (s.max() - s.min())
                s = 1 - s
                s = s.fillna(0)
            elif norm_type == 'inverter_one':
                s = (abs(s - 1) - abs(s - 1).min()) / (abs(s - 1).max() - abs(s - 1).min())
                s = 1 - s
            else:
                s = (s - s.min()) / (s.max() - s.min())

            df[c] = s.fillna(0)
        return df
        
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
    
    def mark_zscore_outliers(self, df, cols, factor=3):
        df = df.copy()
        for c in cols:
            if c not in df.columns:
                continue
            try:
                z = zscore(df[c].fillna(df[c].median()))
                df[f"{c}_outlier_z"] = np.abs(z) > factor
            except Exception:
                df[f"{c}_outlier_z"] = False
        return df

    def detect_nonrecurring(self, df, lucro_col='lucro_liquido', lucro_rec_col='lucro_recorrente_ltm'):
        """
        Marca empresas que tiveram diferença grande entre lucro GAAP e lucro recorrente/LTM.
        Retorna df com coluna 'nonrecurring_flag' e 'recurrence_adjustment' (0..1).
        """
        df = df.copy()
        if lucro_col not in df.columns or lucro_rec_col not in df.columns:
            df['nonrecurring_flag'] = False
            df['recurrence_adjustment'] = 1.0
            return df

        df['diff_pct'] = (df[lucro_col] - df[lucro_rec_col]) / (df[lucro_rec_col].replace(0, np.nan))
        # se a diferença for > 30% do lucro recorrente, marcar
        df['nonrecurring_flag'] = df['diff_pct'].abs() > 0.30
        # ajuste: se flag True, reduz o peso das métricas de profit temporariamente
        df['recurrence_adjustment'] = np.where(df['nonrecurring_flag'], 0.5, 1.0)
        df = df.drop(columns=['diff_pct'])
        return df

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
        
        for metric_col in self.goal:
            z_scores = zscore(df[metric_col].dropna())
            
            
            # df.loc[z_scores > factor, 'outlier'] = True
            
            df.loc[np.abs(z_scores) > factor, 'outlier'] = True
            
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

    def sum_score(self, df_row):
        """
        Calculates the weighted total score based on criteria.
        
        Args:
            df (pd.DataFrame): DataFrame with data.

        Returns:
            float: Score calculated.
        """
        
        # score = 0
        
        # for crit, weight in self.goal.items():
        #     score += df[crit] * weight['weight']

        # return score
        score = 0.0
        adj = df_row.get('recurrence_adjustment', 1.0)
        for crit, meta in self.goal.items():
            w = meta['weight']
            val = df_row.get(crit, 0.0)
            # se critério é de profitability (exemplo), aplique ajuste
            if crit in ['m_líquida', 'roe', 'roic', 'lpa']:
                w = w * adj
            score += val * w
        return score

    # def final_sum_score(self, df_sector, df_general):
    #     """
    #     Calculates the weighted total score joining sector and general scores.
        
    #     Args:
    #         df_sector (pd.DataFrame): DataFrame with sector score.
    #         df_general (pd.DataFrame): DataFrame with general score.

    #     Returns:
    #         float: Final score calculated.
    #     """

    #     score = 0
    #     df_merge = pd.merge(df_sector, df_general, on='ticker', how='inner')

    #     for col, peso in Config.WEIGHTS_ANALYSIS.items():
    #         score += df_merge[col] * peso
            
    #     df_merge['score_final'] = score
            
    #     return df_merge[['ticker', 'score_sector', 'score_general', 'score_final']]

    
    def sector_analyses(self, df, cols_to_normalize):
        """
        Calculates score based on indicators weight splited by sector.

        Args:
            df (pd.DataFrame): DataFrame with data.

        Returns:
            pd.DataFrame: DataFrame with sectorial score.
        """

        # df_sectorized = pd.DataFrame(columns=df.columns)
        # for sector in df['sector'].unique():
        #     df_sector = df[df['sector'] == sector]
        #     df_normalized = self.normalize(df_sector, [i for i in self.goal])
        #     df_normalized['score_sector'] = df_normalized.apply(self.sum_score, axis=1)
        #     df_sectorized = pd.concat([df_sectorized, df_normalized])
        
        # return df_sectorized
        out = []
        for sector, g in df.groupby('sector'):
            g_proc = g.copy()
            g_proc = self.winsorize_df(g_proc, cols_to_normalize)
            g_proc = self.robust_normalize(g_proc, cols_to_normalize)
            g_proc['score_sector'] = g_proc.apply(self.sum_score, axis=1)
            out.append(g_proc)
        return pd.concat(out, ignore_index=True)
            
    def general_analyses(self, df, cols_to_normalize):
        """
        Calculates general score based on indicators weight.

        Args:
            df (pd.DataFrame): DataFrame with data.

        Returns:
            pd.DataFrame: DataFrame with general score.
        """

        # df_normalized = self.normalize(df, [i for i in self.goal])
        # df_normalized['score_general'] = df.apply(self.sum_score, axis=1)

        # return df_normalized
        df_proc = df.copy()
        # winsorize para reduzir outliers extremos
        df_proc = self.winsorize_df(df_proc, cols_to_normalize)
        # normalizar de forma robusta
        df_proc = self.robust_normalize(df_proc, cols_to_normalize)
        # marcar zscore outliers (opcional)
        df_proc = self.mark_zscore_outliers(df_proc, cols_to_normalize)
        # calcular score
        df_proc['score_general'] = df_proc.apply(self.sum_score, axis=1)
        return df_proc
    
    def final_sum_score(self, df_sector, df_general, weight_sector=0.45, weight_general=0.55):
        df_merge = pd.merge(df_sector[['ticker','score_sector']], df_general[['ticker','score_general']],
                            on='ticker', how='inner')
        df_merge['score_final'] = df_merge['score_general'] * weight_general + df_merge['score_sector'] * weight_sector
        return df_merge
