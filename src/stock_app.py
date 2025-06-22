from database import Database
from config import Config
import pandas as pd
import numpy as np
import plotly.express as px

TABLE_NAME = 'stock_data'

def analysis_tickers(type, calcs):
    df_base = Database(TABLE_NAME, Config.DATABASE).view()
    
    max_date = df_base['reference_date'].max()
    df_base = df_base[df_base['reference_date'] == max_date]
    df_base = df_base[df_base['type'] == type]
    
    df, outliers = calcs.outliers_zscore(df_base, 4.5)

    df_sectorized = calcs.sector_analyses(df)
    df_general = calcs.general_analyses(df)

    df_final = calcs.final_sum_score(df_sectorized, df_general)
    df_final = df_final.sort_values(by=['score_final'], ascending=False)

    df_final = pd.merge(df_final, df_base, on='ticker', how='inner')

    return df_final, outliers

def analysis_rank(type, calcs):
    df_base = Database(TABLE_NAME, Config.DATABASE).view()
    
    df_base = df_base[df_base['type'] == type]
    
    unique_dates = df_base['reference_date'].sort_values().unique()
    
    result = []
    for date in unique_dates:
        df_day = df_base[df_base['reference_date'] == date]
        
        df, outliers = calcs.outliers_zscore(df_day, 4)

        df_sectorized = calcs.sector_analyses(df)
        df_general = calcs.general_analyses(df)

        df_final = calcs.final_sum_score(df_sectorized, df_general)
        df_final = df_final.sort_values(by=['score_final'], ascending=False)
        
        df_final['rank'] = df_final['score_final'].rank(ascending=False, method='min').astype(int)
        df_final['date'] = date
        result.append(df_final)
        
    df_all = pd.concat(result, ignore_index=True)

    df_graph = df_all[['ticker', 'rank', 'date']].copy()

    filter_ = df_graph.groupby('ticker')['rank'].mean().reset_index()
    filter_['rank'] = filter_['rank'].rank(ascending=True).astype(int)
    top_tickers = np.array(filter_[filter_['rank'] <= 10]['ticker'])

    df_filtered = df_graph[df_graph['ticker'].isin(top_tickers)]

    return df_filtered

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