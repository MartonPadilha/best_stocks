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

array = np.array([
    -0.59, -1.72, -0.27, -0.55, -0.43, -0.55, 1, 2.86, -5.14, 1.67, 1.43, -3.49, 1.43, -4.92, 0.47, 0.07, 2.7, 0.31, -0.71, 0,
    -0.38, -0.27, -0.17, -0.17, -1.06, 4.66, 0.86, 0.11, 0.71, 0.73, 0.71, 0.86, 0.73, 0.28, 1.57, 1.6, 1.2, -0.31, -2.78, 7.08,
    -4.71, 1.96, 0.72, 4.79, 2.35, -0.27, -0.19, 7.08, 1.35, -1.94, 0.24, -0.46, -3.21, -0.01, -0.42, 3.41, 0.92, 4.84, 2.43, -0.32,
    2.87, 0.55, -1.65, -1.65, -0.89, 0, 5.09, 3.53, -2.5, -2.5, 0.44, 2.19, 2.26, 1.72, 2.48, 3.53, -0.58, 2.93, -6.9, 0.67, 0, 0.27,
    0.72, -0.88, 0.23, 0, 0.36, 1.79, 1.96, 3.84, 0.73, 5, 0.63, 4.56, 2.8, 3.12, -0.24, 0, -3.21, 4.38, 1.58, 1.48, 0.27, 0, 0,
    -3.18, 0.27, -3.18, -3.18, 0.72, 12.22, -0.43, 1.58, 1.64, -3.1, 1.58, 5.67, -20.4, 1.27, 5.03, 1.46, 3.86, 3.06, 3.23, 1.96,
    0.37, 1.08, 2.29, 2.22, 2.89, 2.89, 1.44, -1.4, 2.22, 1.84, -0.35, 3.63, 1.49, 0.77, 3.77, 1.84, 3.94, -3.39, 2.48, 1.88, 0,
    4.46, 2.45, 2.94, -0.15, 1.49, 0, 15.45, 1.63, 1.23, 1.63, 2.32, 1.69, 5.16, 0, 2.48, 2, 3, 5, -1.34, 2, 0, 3.23, 2, 4.09, -0.05,
    3.23, 2.35, 0, 0.16, 0, 7.57, -1.48, -1.05, 2.6, -0.01, 10.11, 2.09, -1.41, 0, 2.09, 0, -0.37, 0.89, 0.89, -0.37, 3.41, 6.7, 2.45,
    3.29, -0.01, 3.29, -0.29, 3.72, 5.47, 7.45, -2.33, 0, 5.03, -4.59, 3.84, 2.61, 0, 0, 1.12, 5.58, 0.91, 5.07, 0, -0.72, 8.49, 5.19,
    4.44, 3.84, 2.22, 4.68, 2.18, -1.33, 3.16, -4.34, 6.04, -150.96, 1.47, 9.24, 2.22, 4.81, 8.86, 4.77, 1.92, 0, 0, 4.86, 0, 2.33,
    0.06, 2.07, -0.37, 5.06, 0.33, 2, 7.28, 5.93, -1.47, 2.73, 7.48, -1.09, 2.43, 6.69, 0.03, 0.03, 5.46, 4.34, 0, -0.39, 0.16, 0.01,
    11.15, 5.05, -26.56, 3.67, 3.67, 3.65, -2.74, 10.48, 4.83, -1.96, 5.39, 93.27, -4.1, -2.72, 6.98, 7.58, -0.76, -12.18, -0.44,
    0.24, 4.04, 7.72, 50.15, 5.48, 6.51, 0, -1.09, 0, -10.25, 7.21, 8.61, 8.94, 13.1
])

# def iqr(data):
#     first_quartil = np.percentile(data, 25)
#     third_quartil = np.percentile(data, 75)
#     iqr = third_quartil - first_quartil
    
#     lower_limit = first_quartil - 1.5 * iqr
#     upper_limit = third_quartil + 1.5 * iqr
#     print(lower_limit, upper_limit)
    
#     return [i for i in data if (i >= lower_limit) & (i <= upper_limit)]
# print(len(array))
# print(len(iqr(array)))
_min, _max = array.min(), array.max()
_range = _max - _min
print(_min, _max, _range)

print(-0.54 - _min)
print((-0.54 - _min) / _range)
print(1 - ((-0.54 - _min) / _range))
