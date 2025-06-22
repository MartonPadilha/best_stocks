class Config():
  STOCK_SUFIX =  [i for i in range(3, 9)]
  FII_SUFIX = [11]
  FOREIGN_SUFIX = [i for i in range(30, 40)]
  
  # WEIGHTS_STOCKS = {
  #   #growth
  #   'cagr_lucros_5_anos': {'weight': 0.12, 'normalization': 'default'},
  #   'cagr_receitas_5_anos': {'weight': 0.1, 'normalization': 'default'},
  #   #profitability
  #   'm_líquida': {'weight': 0.08, 'normalization': 'default'},
  #   'roe': {'weight': 0.1, 'normalization': 'default'},
  #   'roic': {'weight': 0.1, 'normalization': 'default'}, 
  #   'lpa': {'weight': 0.07, 'normalization': 'default'}, 
  #   #indebtedness
  #   'dív_líquida_ebitda': {'weight': 0.08, 'normalization': 'inverter'},
  #   'passivos_ativos': {'weight': 0.05, 'normalization': 'inverter'},
  #   #liquidity
  #   'liq_corrente': {'weight': 0.07, 'normalization': 'default'},
  #   #valuation
  #   'p_l': {'weight': 0.06, 'normalization': 'inverter_zero'},
  #   'p_vp': {'weight': 0.05, 'normalization': 'inverter_one'},
  #   #dividend
  #   'dy': {'weight': 0.12, 'normalization': 'default'}
  # }
  
  WEIGHTS_STOCKS = {
    #growth
    'cagr_lucros_5_anos': {'weight': 0.15, 'normalization': 'default'},
    'cagr_receitas_5_anos': {'weight': 0.1, 'normalization': 'default'},
    #profitability
    'm_líquida': {'weight': 0.06, 'normalization': 'default'},
    'roe': {'weight': 0.11, 'normalization': 'default'},
    'roic': {'weight': 0.1, 'normalization': 'default'}, 
    'lpa': {'weight': 0.04, 'normalization': 'default'}, 
    #indebtedness
    'dív_líquida_ebitda': {'weight': 0.09, 'normalization': 'inverter'},
    'passivos_ativos': {'weight': 0.06, 'normalization': 'inverter'},
    #liquidity
    'liq_corrente': {'weight': 0.05, 'normalization': 'default'},
    #valuation
    'p_l': {'weight': 0.07, 'normalization': 'inverter_zero'},
    'p_vp': {'weight': 0.06, 'normalization': 'inverter_one'},
    #dividend
    'dy': {'weight': 0.11, 'normalization': 'default'}
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
  
  BASE_COLUMNS = ['ticker', 'sector', 'type', 'reference_date']
  
  DATABASE = 'storage/temp_db.sqlite'
  
  TABLES = {
    'stock_data': {
      'insert': 'append',
      'keys': ['ticker', 'reference_date'],
      'file': 'src\input\stock_data.py'
    },
    'news': {
      'insert': 'append',
      'keys': ['url'],
      'file': 'src\input\\news.py'
    },
    'dividends': {
      'insert': 'overwrite',
      'keys': ['ticker'],
      'file': 'src\input\dividends.py'
    },
    'fii_data': {
      'insert': 'overwrite',
      'keys': ['ticker'],
      'file': 'src\input\\fii_data.py'
    },
  }