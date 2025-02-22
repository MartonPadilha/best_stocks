class Config:
    
    STOCK_SUFIX = [3, 4, 5, 6, 7, 8]
    FII_SUFIX = [11]
    
    WEIGHTS_STOCKS =  {
        'p_l': 0.20, 
        'p_vp': 0.20, 
        'dividend_yield': 0.20, 
        'crescimento_lucro': 0.15, 
        'roe': 0.25
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