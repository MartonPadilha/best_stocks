import pytest
import pandas as pd
import numpy as np
from src.analysis import Calcs
import logging

@pytest.fixture
def sample_data():
    #df to tests
    return pd.DataFrame({
        'ticker': ['a', 'b', 'c', 'd', 'e'],
        'p_l': [10, 15, 8, 50, 7],
        'p_vp': [1.2, 1.8, 0.9, 3.0, 0.7],
        'dividend_yield': [5, 3, 6, 2, 8],
        'crescimento_lucro': [10, 20, 5, -3, 15],
        'roe': [15, 20, 12, 8, 25]
    })
    
def test_outliers_iqr(sample_data):
    calcs = Calcs(goal='stock')
    
    df = calcs.outliers_iqr(sample_data, factor=1.5)
    print(df)
    df = calcs.outliers_zscore(sample_data, factor=3)
    print(df)
    assert len(df) == 4
    
def test_normalize(sample_data):
    calcs = Calcs(goal='stock')
    
    df = calcs.normalize(sample_data, ['p_l', 'p_vp', 'dividend_yield'])
    
    assert df[['p_l', 'p_vp', 'dividend_yield']].between(0, 1).all().all()
    
def test_calc_general(sample_data):
    calcs = Calcs(goal='stock')
    
    df = calcs.normalize(sample_data, [col for col in sample_data.columns if col != 'ticker'])
    
    df = calcs.general_analyses(df)
    
    max_result = round(df['score_general'].max(), 3)
    max_expected = 0.596
    
    assert max_result == max_expected
    