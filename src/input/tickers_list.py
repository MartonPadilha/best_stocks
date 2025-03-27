import requests
import os
from dotenv import load_dotenv

load_dotenv()

def list_codes(action):
    url_base = 'https://brapi.dev/api'
    full_url = url_base + action
    token = os.getenv("TOKEN_BRAPI")
    params = {
        'token': token
    }
    response = requests.get(full_url, params=params)
    data = response.json()
    
    _list = [i['stock'] for i in data['stocks'] if not i['stock'].endswith('F')]
    
    return _list

def create_file(string):
    lista_write = open("storage/tickers_list.txt", "a")
    lista_write.write(str(string))
    lista_write.close()

def main():
    list_stocks = list_codes('/quote/list')
    create_file(list_stocks)
    return

if __name__ == "__main__":
    main()

