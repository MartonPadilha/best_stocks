import os


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
    'm_líquida': {'weight': 0.07, 'normalization': 'default'},
    'roe': {'weight': 0.1, 'normalization': 'default'},
    'roic': {'weight': 0.14, 'normalization': 'default'}, 
    'lpa': {'weight': 0.04, 'normalization': 'default'}, 
    #indebtedness
    'dív_líquida_ebitda': {'weight': 0.08, 'normalization': 'inverter'},
    'passivos_ativos': {'weight': 0.03, 'normalization': 'inverter'},
    #liquidity
    'liq_corrente': {'weight': 0.04, 'normalization': 'default'},
    #valuation
    'p_l': {'weight': 0.12, 'normalization': 'inverter_zero'},
    'p_vp': {'weight': 0.10, 'normalization': 'inverter_one'},
    #dividend
    'dy': {'weight': 0.03, 'normalization': 'default'}
  }
  
  WEIGHTS_FIIS = {
    'dy': {'weight': 0.4, 'normalization': 'default'},
    'p_vp': {'weight': 0.3, 'normalization': 'default'},
    'peg_ratio': {'weight': 0.3, 'normalization': 'default'}
  }
  
  INDICATOR_CAPS = {
    'dy': 15.0,
    'cagr_lucros_5_anos': 50.0,
    'cagr_receitas_5_anos': 50.0,
  }

  MOMENTUM_WEIGHT = 0.10

  WEIGHTS_ANALYSIS = {
    'score_general': 0.65,
    'score_sector': 0.35
  }
  
  BASE_COLUMNS = ['ticker', 'sector', 'type', 'reference_date']
  
  DATABASE = os.getenv('DATABASE_PATH', 'storage/temp_db.sqlite')

  TABLES = {
    'stock_data': {
      'insert': 'append',
      'keys': ['ticker', 'reference_date'],
      'file': 'src/input/stock_data.py',
      'depends_on': []
    },
    'news': {
      'insert': 'append',
      'keys': ['url'],
      'file': 'src/input/news.py',
      'depends_on': ['stock_data']
    },
    'dividends': {
      'insert': 'overwrite',
      'keys': ['ticker'],
      'file': 'src/input/dividends.py',
      'depends_on': []
    },
    'fii_data': {
      'insert': 'overwrite',
      'keys': ['ticker'],
      'file': 'src/input/fii_data.py',
      'depends_on': []
    },
  }