class Config:
    
    STOCK_SUFIX = [3, 4, 5, 6, 7, 8]
    FII_SUFIX = [11]
    
    WEIGHTS_STOCKS =  {
        'p_l': 0.15, 
        'p_vp': 0.15, 
        'dividend_yield': 0.25, 
        'crescimento_lucro': 0.25, 
        'roe': 0.2
    }
    
    WEIGHTS_FIIS =  {
        'dividend_yield': 0.4,
        'p_vp':  0.3,
        'payout_ratio':  0.3,
    }
    
    WEIGHTS_ANALYSIS =  {
        'score_general': 0.6, 
        'score_sector': 0.4
    }
    
    BASE_COLUMNS = [
        'ticker', 'sector'
    ]
    
    DATABASE = {
        'name': 'stock_data',
        'table': 'temp_db.sqlite'
    }