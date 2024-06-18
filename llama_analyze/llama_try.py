import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv
from ollama import AsyncClient

def get_stock_price(stock_id):
    url = f'https://tw.stock.yahoo.com/quote/{stock_id}'  # Yahoo Finance stock URL
    web = requests.get(url)  # Get the webpage content
    soup = BeautifulSoup(web.text, "html.parser")  # Convert content
    title = soup.find('h1').get_text()  # Get title
    current_price = soup.select('.Fz\(32px\)')[0].get_text()  # Get current price
    change = soup.select('.Fz\(20px\)')[0].get_text()  # Get price change
    status = ''  # Status: up, down, or flat

    try:
        # If the div with id main-0-QuoteHeader-Proxy contains class C($c-trend-down),
        # it indicates a downtrend
        if soup.select('#main-0-QuoteHeader-Proxy')[0].select('.C($c-trend-down)')[0]:
            status = '-'
    except:
        try:
            # If the div with id main-0-QuoteHeader-Proxy contains class C($c-trend-up),
            # it indicates an uptrend
            if soup.select('#main-0-QuoteHeader-Proxy')[0].select('.C($c-trend-up)')[0]:
                status = '+'
        except:
            # If neither class is found, it indicates a flat trend
            status = '▬'

    return f'{title} : {current_price} ( {status}{change} )'  # Return the formatted string

def parse_output(output):
    lines = output.split('\n')
    result = {}
    for line in lines:
        if line.startswith('1. **Bullish or bearish in the next six months:**'):
            result['Bullish/Bearish'] = line.split(':')[1].strip().strip('**')
        elif line.startswith('2. **Recommended buying price:**'):
            result['Recommended buying price'] = line.split(':')[1].strip().strip('**')
        elif line.startswith('3. **Recommended selling price:**'):
            result['Recommended selling price'] = line.split(':')[1].strip().strip('**')
        elif line.startswith('4. **Recommended holding period:**'):
            result['Recommended holding period'] = line.split(':')[1].strip().strip('**').split()[0]  # Extract only the number of months
        elif line.startswith('5. **Stop-loss strategy:**'):
            result['Stop-loss strategy'] = line.split(':')[1].strip().strip('**').split()[-1]  # Extract only the stop-loss price
    return result

async def chat():
    stock_id = 2330
    # 讀取CSV檔案
    data_bps = pd.read_csv('year_bps.csv', index_col=0)  
    data_roe = pd.read_csv('year_roe.csv', index_col=0)
    data_Share_capital = pd.read_csv('year_Share_capital.csv', index_col=0)
    stock_price = get_stock_price(stock_id)
    # 找到對應資料
    bps_value = data_bps.loc[2023, str(stock_id)]
    roe = data_roe.loc[2023, str(stock_id)]
    capital = data_Share_capital.loc[2023, str(stock_id)]

    message = {
        'role': 'user',
        'content': f'''Based on the data I found, the stock price of {stock_id} is {stock_price}, the BPS (book value per share) for the past year is ({bps_value}), the capital for the past year is ({capital}), and the ROE (return on equity) for the past year is ({roe}%). \
        Assume you are a stock analyst + \
        , provide answers to the following questions: 1. Will it be bullish or bearish in the next six months? 2. Recommended buying price? 3. Recommended selling price? 4. Recommended holding period? 5. Stop-loss strategy. + \
        The answer format should be 1. Answer 2. Answer 3. Answer 4. Answer (number of months) 5. Answer. Do not provide additional information. A standard response example is as follows + \
        1. **Bullish or bearish in the next six months:** (Bullish/Bearish)  \
        2. **Recommended buying price:** (Price)  \
        3. **Recommended selling price:** (Price) \
        4. **Recommended holding period:** (months) \
        5. **Stop-loss strategy:**'''
    }

    print(message)

    # 將輸出存成txt檔案
    with open('output.txt', 'w', encoding='utf-8') as f:
        async for part in await AsyncClient().chat(model='llama3:8b', messages=[message], stream=True, options={"temperature": 0.8}):
            f.write(part['message']['content'])

    # 解析輸出結果
    with open('output.txt', 'r', encoding='utf-8') as f:
        output = f.read()
        parsed_result = parse_output(output)

    # 將結果寫入CSV檔案
    csv_file = 'output.csv'
    fieldnames = ['Bullish/Bearish', 'Recommended buying price', 'Recommended selling price', 'Recommended holding period', 'Stop-loss strategy']

    # 檢查CSV檔案是否存在
    try:
        with open(csv_file, 'x', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    except FileExistsError:
        pass

    # 將解析結果寫入CSV檔案
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(parsed_result)

    # 輸出結果到終端
    print(parsed_result)

asyncio.run(chat())

