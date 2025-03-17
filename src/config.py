class Config():
  STOCK_SUFIX =  [i for i in range(3, 9)]
  FII_SUFIX = [11]
  FOREIGN_SUFIX = [i for i in range(30, 40)]
  
  WEIGHTS_STOCKS = {
    #growth
    'cagr_lucros_5_anos': {'weight': 0.15, 'normalization': 'default'},
    'cagr_receitas_5_anos': {'weight': 0.12, 'normalization': 'default'},
    #profitability
    'm_líquida': {'weight': 0.08, 'normalization': 'default'},
    'roe': {'weight': 0.12, 'normalization': 'default'},
    'lpa': {'weight': 0.08, 'normalization': 'default'}, 
    #indebtedness
    'dív_líquida_ebitda': {'weight': 0.13, 'normalization': 'inverter'},
    'passivos_ativos': {'weight': 0.04, 'normalization': 'inverter'},
    #liquidity
    'liq_corrente': {'weight': 0.08, 'normalization': 'default'},
    #valuation
    'p_l': {'weight': 0.08, 'normalization': 'inverter_zero'},
    'p_vp': {'weight': 0.04, 'normalization': 'inverter_one'},
    #dividend
    'dy': {'weight': 0.08, 'normalization': 'default'}
  }
  
  WEIGHTS_FIIS = {
    'dy': {'weight': 0.4, 'normalization': 'default'},
    'p_vp': {'weight': 0.3, 'normalization': 'default'},
    'peg_ratio': {'weight': 0.3, 'normalization': 'default'}
  }
  
  WEIGHTS_ANALYSIS = {
    'score_general': 0.6,
    'score_sector': 0.4
  }
  
  BASE_COLUMNS = ['ticker', 'sector', 'type']
  
  DATABASE = 'storage/temp_db.sqlite'