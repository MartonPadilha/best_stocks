from analysis import Calcs
from database import Database
from config import Config
import pandas as pd

TABLE_NAME = 'fii_data'

def show_fiis():
    df_base = Database(TABLE_NAME, Config.DATABASE).view()
    
    return df_base