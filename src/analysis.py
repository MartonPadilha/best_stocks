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

    def cap_indicators(self, df, caps):
        df = df.copy()
        for col, cap_value in caps.items():
            if col not in df.columns:
                continue
            mask = df[col] > cap_value
            if mask.any():
                excess = df.loc[mask, col] - cap_value
                df.loc[mask, col] = cap_value + np.log1p(excess)
        return df

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
            elif norm_type == 'inverter_one':
                s = (abs(s - 1) - abs(s - 1).min()) / (abs(s - 1).max() - abs(s - 1).min())
                s = 1 - s
            else:
                s = (s - s.min()) / (s.max() - s.min())

            # Missing explícito: NaN vira 0.5 (neutro), não 0 (pior).
            # Dado faltante não deve penalizar — apenas não contribui.
            df[c] = s.fillna(0.5)
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
        score = 0.0
        adj = df_row.get('recurrence_adjustment', 1.0)
        roe_roic_pen = df_row.get('roe_roic_penalty', 1.0)
        for crit, meta in self.goal.items():
            w = meta['weight']
            val = df_row.get(crit, 0.0)
            if crit in ['m_líquida', 'roe', 'roic', 'lpa']:
                # profitability é penalizado por recurrence adjustment E por spread ROE/ROIC
                w = w * adj * roe_roic_pen
            score += val * w
        return score

    def reconcile_roe_roic(self, df):
        """Penaliza ROE muito acima de ROIC — spread indica alavancagem/encolhimento de equity, não qualidade.

        Adiciona coluna 'roe_roic_penalty' (0 a 1) e ajuste de score de profitability.
        """
        df = df.copy()
        if 'roe' not in df.columns or 'roic' not in df.columns:
            df['roe_roic_penalty'] = 1.0
            return df
        roe = pd.to_numeric(df['roe'], errors='coerce')
        roic = pd.to_numeric(df['roic'], errors='coerce')
        spread = roe - roic
        # spread saudável: < 10pp (roe levemente acima de roic é normal por alavancagem moderada)
        # spread suspeito: > 20pp — equity encolhendo ou ganho não recorrente inflando ROE
        penalty = np.where(
            spread.isna() | roic.isna(),
            1.0,
            np.clip(1.0 - (spread - 10) / 30, 0.3, 1.0)
        )
        df['roe_roic_penalty'] = penalty
        return df

    def compute_trend(self, df_hist, indicators, date_col='reference_date', ticker_col='ticker'):
        """Calcula tendência (melhorando/piorando) de indicadores ao longo do histórico.

        Retorna DataFrame com ticker + trend_<indicator> em [-1, 1].
        - +1: indicador melhorando consistentemente
        - -1: indicador piorando
        - 0: estável ou sem histórico suficiente
        """
        df = df_hist.copy()
        if date_col not in df.columns or ticker_col not in df.columns:
            return pd.DataFrame(columns=[ticker_col] + [f"trend_{i}" for i in indicators])
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values([ticker_col, date_col])
        out = []
        for ticker, g in df.groupby(ticker_col):
            row = {ticker_col: ticker}
            for ind in indicators:
                col = ind
                if col not in g.columns:
                    row[f"trend_{ind}"] = 0.0
                    continue
                series = pd.to_numeric(g[col], errors='coerce').dropna()
                if len(series) < 3:
                    row[f"trend_{ind}"] = 0.0
                    continue
                first_half = series.iloc[:len(series)//2].mean()
                second_half = series.iloc[len(series)//2:].mean()
                denom = abs(first_half) if abs(first_half) > 1e-9 else 1.0
                pct_change = (second_half - first_half) / denom
                row[f"trend_{ind}"] = float(np.clip(pct_change, -1, 1))
            out.append(row)
        return pd.DataFrame(out)

    def detect_dy_value_trap(self, df_hist, date_col='reference_date', ticker_col='ticker'):
        """Marca DY alto causado por queda de preço (value trap) em vez de crescimento de dividendo.

        Retorna DataFrame com ticker + 'dy_value_trap_flag' (bool) + 'dy_trap_penalty' (0 a 1).
        """
        df = df_hist.copy()
        if date_col not in df.columns or 'dy' not in df.columns or 'p_vp' not in df.columns:
            return pd.DataFrame(columns=[ticker_col, 'dy_value_trap_flag', 'dy_trap_penalty'])
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values([ticker_col, date_col])
        out = []
        for ticker, g in df.groupby(ticker_col):
            dy = pd.to_numeric(g['dy'], errors='coerce').dropna()
            pvp = pd.to_numeric(g['p_vp'], errors='coerce').dropna()
            if dy.empty or pvp.empty or len(dy) < 2 or len(pvp) < 2:
                out.append({ticker_col: ticker, 'dy_value_trap_flag': False, 'dy_trap_penalty': 1.0})
                continue
            dy_recent = dy.iloc[-1]
            dy_past = dy.iloc[0]
            pvp_recent = pvp.iloc[-1]
            pvp_past = pvp.iloc[0]
            dy_grew = dy_recent > dy_past * 1.3 if dy_past > 0 else False
            price_fell = pvp_recent < pvp_past * 0.85 if pvp_past > 0 else False
            high_dy = dy_recent > 12
            trap = dy_grew and price_fell and high_dy
            penalty = 0.3 if trap else 1.0
            out.append({ticker_col: ticker, 'dy_value_trap_flag': bool(trap), 'dy_trap_penalty': float(penalty)})
        return pd.DataFrame(out)


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
        Score por setor, normalizando apenas contra peers saudáveis (sem prejuízo).

        Empresas com prejuízo (ROE < 0 ou P/L < 0) são excluídas da referência
        de normalização setorial para evitar premiar "melhor num cemitério".
        Ainda recebem score, mas normalizadas contra o subconjunto saudável.
        """
        out = []
        for sector, g in df.groupby('sector'):
            g_proc = g.copy()
            # Referência saudável: ROE > 0 e P/L > 0 (quando disponíveis)
            roe = pd.to_numeric(g_proc.get('roe'), errors='coerce')
            pl = pd.to_numeric(g_proc.get('p_l'), errors='coerce')
            healthy_mask = (roe > 0) & (pl > 0)
            if healthy_mask.sum() >= 3:
                # Normaliza apenas contra peers saudáveis, depois aplica a todos do setor
                healthy_ref = g_proc[healthy_mask].copy()
                healthy_ref = self.winsorize_df(healthy_ref, cols_to_normalize)
                healthy_ref = self.robust_normalize(healthy_ref, cols_to_normalize)
                # Para não-saudáveis, atribui valor neutro (0.5) nos cols normalizados
                unhealthy = g_proc[~healthy_mask].copy()
                for c in cols_to_normalize:
                    if c in unhealthy.columns:
                        unhealthy[c] = 0.5
                g_proc = pd.concat([healthy_ref, unhealthy], ignore_index=True)
            else:
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
