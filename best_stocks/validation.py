import yfinance as yf
import pandas as pd
from IPython.display import display
import numpy as np

# stock = 'VSTE3.SA'
# dados = []
# info = yf.Ticker(stock).info

# # stock = 'HSML11.SA'

# dados.append({
#     'ticker': stock,
#     'sector': info.get('sector', ''),
#     'p_l': info.get('forwardPE', 0) or 0,
#     'p_vp': info.get('priceToBook', 0) or 0,
#     'dividend_yield': (info.get('dividendYield', 0) or 0) * 100,
#     'crescimento_lucro': (info.get('earningsGrowth', 0) or 0) * 100,
#     'roe': (info.get('returnOnEquity', 0) or 0) * 100,
#     'payout_ratio': info.get("payoutRatio") or 0,
# })
# print(info)

# arr = np.array([10.373271, 4.9050493, 4.4619102, 12.300663, 11.093246, 4.6197658, 6.1585493, 7.791472, 12.045938])
# first_quartil = np.percentile(arr, 25)
# third_quartil = np.percentile(arr, 75)
# iqr = third_quartil - first_quartil
# print(first_quartil, third_quartil, iqr)

array = [10, 15, 8, 50, 7]

def iqr(data):
    first_quartil = np.percentile(data, 25)
    third_quartil = np.percentile(data, 75)
    iqr = third_quartil - first_quartil
    
    lower_limit = first_quartil - 1.5 * iqr
    upper_limit = third_quartil + 1.5 * iqr
    print(lower_limit, upper_limit)
    
    return [i for i in data if (i >= lower_limit) & (i <= upper_limit)]
print(len(array))
print(len(iqr(array)))

