from database import Database
from config import Config
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

TABLE_NAME = 'stock_data'

# def analysis_tickers(type, calcs):
#     df_base = Database(TABLE_NAME, Config.DATABASE).view()
    
#     max_date = df_base['reference_date'].max()
#     df_base = df_base[df_base['reference_date'] == max_date]
#     df_base = df_base[df_base['type'] == type]
    
#     df, outliers = calcs.outliers_zscore(df_base, 4.5)

#     df_sectorized = calcs.sector_analyses(df)
#     df_general = calcs.general_analyses(df)

#     df_final = calcs.final_sum_score(df_sectorized, df_general)
#     df_final = df_final.sort_values(by=['score_final'], ascending=False)

#     df_final = pd.merge(df_final, df_base, on='ticker', how='inner')

#     return df_final, outliers

# def analysis_rank(type, calcs, period='all'):
#     df_base = Database(TABLE_NAME, Config.DATABASE).view()
#     df_base = df_base[df_base['type'] == type]
    
#     # Ordena e pega datas únicas
#     unique_dates = df_base['reference_date'].sort_values().unique()
#     if len(unique_dates) == 0:
#         st.warning("Nenhum dado encontrado para o tipo selecionado.")
#         return pd.DataFrame()
    
#     # Determina o período máximo com base na última data
#     last_date = pd.to_datetime(unique_dates[-1])
#     if period != 'all':
#         days_map = {
#             '7d': 7,
#             '30d': 30,
#             '90d': 90,
#             '1y': 365
#         }
#         days = days_map.get(period, 0)
#         start_date = last_date - timedelta(days=days)
#         df_base = df_base[pd.to_datetime(df_base['reference_date']) >= start_date]

#     unique_dates = df_base['reference_date'].sort_values().unique()
#     result = []

#     for date in unique_dates:
#         df_day = df_base[df_base['reference_date'] == date]
        
#         df, outliers = calcs.outliers_zscore(df_day, 4)
#         df_sectorized = calcs.sector_analyses(df)
#         df_general = calcs.general_analyses(df)
#         df_final = calcs.final_sum_score(df_sectorized, df_general)
#         df_final = df_final.sort_values(by=['score_final'], ascending=False)
        
#         df_final['rank'] = df_final['score_final'].rank(ascending=False, method='min').astype(int)
#         df_final['date'] = date
#         result.append(df_final)
        
#     df_all = pd.concat(result, ignore_index=True)
#     df_graph = df_all[['ticker', 'rank', 'date']].copy()

#     # Ranking médio
#     filter_ = df_graph.groupby('ticker')['rank'].mean().reset_index()
#     filter_['rank'] = filter_['rank'].rank(ascending=True).astype(int)
    
#     top_tickers = np.array(filter_[filter_['rank'] <= 10]['ticker'])
#     df_filtered = df_graph[df_graph['ticker'].isin(top_tickers)]

#     return df_filtered

def plot_rank(df, axle_x, axle_y):
    fig = px.line(
        df,
        x=axle_x,
        y=axle_y,
        color='ticker',
        title='Evolução do Rank por Ticker',
        markers=True
    )
    return fig.update_yaxes(autorange='reversed')

def show_dividends():
    df_base = Database('dividends', Config.DATABASE).view()
    
    df_base['total_value'] = df_base.groupby('ticker')['value'].transform('sum')

    return df_base

def show_news():
    df_base = Database('news', Config.DATABASE).view()
    df_base = df_base[df_base['score'].notnull()]
    df_base['score'] = df_base['score'].astype(int)
    df_base['avg_score'] = df_base.groupby('ticker')['score'].transform('mean')

    return df_base


def _ensure_types(df):
    df = df.copy()
    # garantir nome de data uniforme
    if 'reference_date' not in df.columns and 'date' in df.columns:
        df = df.rename(columns={'date': 'reference_date'})
    if 'reference_date' in df.columns:
        df['reference_date'] = pd.to_datetime(df['reference_date'], errors='coerce')
    # coerção numérica mínima para colunas comuns
    numeric_cols = [
        'price', 'p_l', 'p_vp', 'dy', 'm_líquida', 'roe', 'roic',
        'liq_corrente', 'dív_líquida_ebitda', 'lucro_liquido', 'ebitda',
        'receita', 'passivos_ativos'
    ]
    for c in numeric_cols:
        if c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str).str.replace(r'[^\d,.\-eE]', '', regex=True).str.replace(',', '.')
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df


def analysis_tickers(type, calcs):
    # carrega todo o histórico (view retorna a tabela completa)
    df_hist = Database(TABLE_NAME, Config.DATABASE).view()
    if df_hist is None or df_hist.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_hist = _ensure_types(df_hist)

    # gerar rolling features LTM/rolling (Calcs.add_rolling_features deve existir)
    rolling_feats = calcs.add_rolling_features(df_hist, price_col='price', date_col='reference_date', ticker_col='ticker')

    # snapshot: pegar último registro por ticker do histórico (mantém sector, type, etc)
    df_base = df_hist.sort_values(['ticker', 'reference_date']).groupby('ticker').tail(1).reset_index(drop=True)
    df_base = df_base[df_base['type'] == type].reset_index(drop=True)

    # merge snapshot com rolling_feats
    df_latest = pd.merge(df_base, rolling_feats, on='ticker', how='left', suffixes=('', '_roll'))

    # detectar eventos não recorrentes (usa lucros LTM gerados por add_rolling_features)
    df_latest = calcs.detect_nonrecurring(df_latest, lucro_col='lucro_liquido', lucro_rec_col='lucro_liquido_ltm')

    # mapear métricas do seu WEIGHTS para as colunas rolling/LTM quando existirem
    win_short = calcs.temporal_windows[0] if hasattr(calcs, 'temporal_windows') else 30
    win_mid = calcs.temporal_windows[1] if hasattr(calcs, 'temporal_windows') else 90
    win_long = calcs.temporal_windows[2] if hasattr(calcs, 'temporal_windows') else 180

    metric_map = {
        'p_l': f"p_l_{win_mid}d_mean" if f"p_l_{win_mid}d_mean" in df_latest.columns else 'p_l',
        'p_vp': f"p_vp_{win_mid}d_mean" if f"p_vp_{win_mid}d_mean" in df_latest.columns else 'p_vp',
        'dy': f"dy_{win_short}d_mean" if f"dy_{win_short}d_mean" in df_latest.columns else 'dy',
        'm_líquida': f"m_líquida_{win_long}d_median" if f"m_líquida_{win_long}d_median" in df_latest.columns else 'm_líquida',
        'roe': f"roe_{win_long}d_median" if f"roe_{win_long}d_median" in df_latest.columns else 'roe',
        'roic': f"roic_{win_long}d_median" if f"roic_{win_long}d_median" in df_latest.columns else 'roic',
        'dív_líquida_ebitda': f"dív_líquida_ebitda_{win_long}d_median" if f"dív_líquida_ebitda_{win_long}d_median" in df_latest.columns else 'dív_líquida_ebitda',
        'liq_corrente': f"liq_corrente_{win_long}d_median" if f"liq_corrente_{win_long}d_median" in df_latest.columns else 'liq_corrente',
        'cagr_lucros_5_anos': 'cagr_lucros_5_anos',
        'cagr_receitas_5_anos': 'cagr_receitas_5_anos',
        'lpa': 'lpa',
        'passivos_ativos': 'passivos_ativos'
    }

    # construir df_scoring com colunas esperadas pelo Calcs
    df_scoring = pd.DataFrame()
    df_scoring['ticker'] = df_latest['ticker']
    df_scoring['sector'] = df_latest.get('sector', np.nan)
    for goal_metric in calcs.goal.keys():
        mapped = metric_map.get(goal_metric, goal_metric)
        df_scoring[goal_metric] = df_latest.get(mapped, 0.0).astype(float) if mapped in df_latest.columns else 0.0

    df_scoring['recurrence_adjustment'] = df_latest.get('recurrence_adjustment', 1.0)

    # Outliers (antes do score) — ajuste o fator se necessário
    df_no_out, df_outliers = calcs.outliers_zscore(df_scoring.copy(), factor=4.5)

    # colunas que vamos normalizar (baseadas nos seus pesos)
    cols_to_normalize = list(calcs.goal.keys())

    # análises e ranking (passando os cols para as funções de Calcs)
    df_sectorized = calcs.sector_analyses(df_no_out, cols_to_normalize)
    df_general = calcs.general_analyses(df_no_out, cols_to_normalize)
    df_final = calcs.final_sum_score(df_sectorized, df_general)
    df_final = df_final.sort_values(by=['score_final'], ascending=False)

    df_display = pd.merge(df_final, df_base, on='ticker', how='left')
    return df_display.reset_index(drop=True), df_outliers.reset_index(drop=True)


def analysis_rank(type, calcs, period='all'):
    df_hist = Database(TABLE_NAME, Config.DATABASE).view()
    if df_hist is None or df_hist.empty:
        return pd.DataFrame()

    df_hist = _ensure_types(df_hist)
    df_hist = df_hist[df_hist['type'] == type].copy()

    unique_dates = np.sort(df_hist['reference_date'].dropna().unique())
    if len(unique_dates) == 0:
        return pd.DataFrame()

    last_date = pd.to_datetime(unique_dates[-1])
    if period != 'all':
        days_map = {'7d': 7, '30d': 30, '90d': 90, '1y': 365}
        days = days_map.get(period, 0)
        start_date = last_date - timedelta(days=days)
        df_hist = df_hist[df_hist['reference_date'] >= start_date]

    unique_dates = np.sort(df_hist['reference_date'].dropna().unique())
    result = []

    for date in unique_dates:
        df_day = df_hist[df_hist['reference_date'] == date].copy()
        if df_day.empty:
            continue

        # construir df_scoring com colunas pontuais do dia (histórico)
        df_scoring = pd.DataFrame()
        df_scoring['ticker'] = df_day['ticker']
        df_scoring['sector'] = df_day.get('sector', np.nan)
        for goal_metric in calcs.goal.keys():
            if goal_metric in df_day.columns:
                df_scoring[goal_metric] = df_day[goal_metric].astype(float)
            else:
                df_scoring[goal_metric] = 0.0
        df_scoring['recurrence_adjustment'] = 1.0

        df_no_out, _ = calcs.outliers_zscore(df_scoring.copy(), factor=4)
        cols_to_normalize = list(calcs.goal.keys())
        df_sectorized = calcs.sector_analyses(df_no_out, cols_to_normalize)
        df_general = calcs.general_analyses(df_no_out, cols_to_normalize)
        df_final = calcs.final_sum_score(df_sectorized, df_general)
        df_final = df_final.sort_values(by=['score_final'], ascending=False)

        df_final['rank'] = df_final['score_final'].rank(ascending=False, method='min').astype(int)
        df_final['date'] = date
        result.append(df_final[['ticker', 'rank', 'date']])

    if not result:
        return pd.DataFrame()

    df_all = pd.concat(result, ignore_index=True)
    avg_rank = df_all.groupby('ticker')['rank'].mean().reset_index()
    avg_rank['rank'] = avg_rank['rank'].rank(ascending=True).astype(int)
    top_tickers = avg_rank[avg_rank['rank'] <= 10]['ticker'].values
    df_filtered = df_all[df_all['ticker'].isin(top_tickers)].copy()
    return df_filtered