import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from database import Database
from config import Config
import ast
import yfinance as yf

info = yf.Ticker('PETR4.SA').info
print([i in i for range(30, 39)])