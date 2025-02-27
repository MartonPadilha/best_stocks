class Config():
  STOCK_SUFIX =  [3, 4, 5, 6, 7, 8]
  
  FII_SUFIX = [11]
  
  WEIGHTS_STOCKS = {
    'crescimento_lucro': {'weight': 0.18, 'normalization': 'default'},
    'crescimento_receita': {'weight': 0.12, 'normalization': 'default'},
    'm_liquida': {'weight': 0.08, 'normalization': 'default'},
    'lpa': {'weight': 0.08, 'normalization': 'default'}, 
    'roe': {'weight': 0.1, 'normalization': 'default'},
    'div_liq_ebitda': {'weight': 0.15, 'normalization': 'inverter'},
    'liq_corrent': {'weight': 0.08, 'normalization': 'default'},
    'passivos_ativos': {'weight': 0.04, 'normalization': 'inverter'},
    'p_l': {'weight': 0.08, 'normalization': 'inverter_zero'},
    'p_vp': {'weight': 0.04, 'normalization': 'inverter_one'},
    'dividend_yield': {'weight': 0.05, 'normalization': 'default'}
  }
  
  # WEIGHTS_STOCKS = {
  #   'crescimento_lucro': {'weight': 0.2, 'normalization': 'default'},
  #   # 'crescimento_receita': {'weight': 0.12, 'normalization': 'default'},
  #   # 'm_liquida': {'weight': 0.08, 'normalization': 'default'},
  #   # 'lpa': {'weight': 0.08, 'normalization': 'default'}, 
  #   'roe': {'weight': 0.25, 'normalization': 'default'},
  #   # 'div_liq_ebitda': {'weight': 0.15, 'normalization': 'inverter'},
  #   # 'liq_corrent': {'weight': 0.08, 'normalization': 'default'},
  #   # 'passivos_ativos': {'weight': 0.04, 'normalization': 'inverter'},
  #   'p_l': {'weight': 0.15, 'normalization': 'inverter_zero'},
  #   'p_vp': {'weight': 0.15, 'normalization': 'inverter_one'},
  #   'dividend_yield': {'weight': 0.25, 'normalization': 'default'}
  # }
  
  WEIGHTS_FIIS = {
    'dividend_yield': {'weight': 0.4, 'normalization': 'default'},
    'p_vp': {'weight': 0.3, 'normalization': 'default'},
    'payout_ratio': {'weight': 0.3, 'normalization': 'default'}
  }
  
  WEIGHTS_ANALYSIS = {
      'score_general': 0.55,
      'score_sector': 0.45
      }
  
  BASE_COLUMNS = ['ticker', 'sector']
  
  DATABASE = {
      'name': 'stock_data',
      'table': 'temp_db.sqlite'
      }