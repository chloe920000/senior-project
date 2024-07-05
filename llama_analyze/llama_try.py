import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv
from ollama import AsyncClient
import datetime

def get_stock_price(stock_id):
    url = f'https://tw.stock.yahoo.com/quote/{stock_id}'  # Yahoo Finance stock URL
    web = requests.get(url)  # Get the webpage content
    soup = BeautifulSoup(web.text, "html.parser")  # Convert content
    title = soup.find('h1').get_text()  # Get title
    current_price = soup.select('.Fz\(32px\)')[0].get_text()  # Get current price
    change = soup.select('.Fz\(20px\)')[0].get_text()  # Get price change
    status = ''  # Status: up, down, or flat

    try:
        if soup.select('#main-0-QuoteHeader-Proxy')[0].select('.C($c-trend-down)')[0]:
            status = '-'
    except:
        try:
            if soup.select('#main-0-QuoteHeader-Proxy')[0].select('.C($c-trend-up)')[0]:
                status = '+'
        except:
            status = '▬'

    return f'{title} : {current_price} ( {status}{change} )'  # Return the formatted string

def parse_output(output):
    lines = output.split('\n')
    result = {}
    for line in lines:
        if line.startswith('1. Will it be bullish or bearish in the next six months?:'):
            result['Bullish/Bearish'] = line.split(':')[1].strip()
        elif line.startswith('2. Recommended buying price, considering a margin of error of +/- 5%?:'):
            result['Recommended buying price'] = line.split(':')[1].strip()
        elif line.startswith('3. Recommended selling price, assuming a stop-loss strategy with a maximum loss of 10%?:'):
            result['Recommended selling price'] = line.split(':')[1].strip()
        elif line.startswith('4. Recommended holding period for this investment? (months):'):
            result['Recommended holding period'] = line.split(':')[1].strip()
        elif line.startswith('5. Suggested stop-loss strategy? What would be your criteria for triggering a sell order?:'):
            result['Stop-loss strategy'] = line.split(':')[1].strip()
    return result

async def chat():
    stock_id = 2002
    # 讀取CSV檔案
    data_bps = pd.read_csv('year_bps.csv', index_col=0)  
    data_roe = pd.read_csv('year_roe.csv', index_col=0)
    data_Share_capital = pd.read_csv('year_Share_capital.csv', index_col=0)

    for _ in range(10):  # 循環10次
        stock_price = get_stock_price(stock_id)
        # 找到對應資料
        bps_value = data_bps.loc[2023, str(stock_id)]
        roe = data_roe.loc[2023, str(stock_id)]
        capital = data_Share_capital.loc[2023, str(stock_id)]

        message = {
            'role': 'user',
            'content': f'''Evaluate the stock price of TWSE{stock_id}.  based on the following data:

* Current price: {stock_price}
* BPS (book value per share): {bps_value}
* Capital: {capital}
* ROE (return on equity): {roe}%


Provide additional context about the company, industry, and market trends.

Assume you are a stock analyst, provide answers to the following questions (Only answer the following questions, do not give suggestions or analysis):

1. Will it be bullish or bearish in the next six months?
2. Recommended buying price, considering a margin of error of +/- 5%?
3. Recommended selling price, assuming a stop-loss strategy with a maximum loss of 10%?
4. Recommended holding period for this investment?(months)
5. Suggested stop-loss strategy? What would be your criteria for triggering a sell order?

Criteria for evaluation:

* A "bullish" market is defined as an increase of at least 10% in the stock's price over the next six months.
* A "bearish" market is defined as a decrease of at least 15% in the stock's price over the next six months.
* If it is bullish, usually the selling price will be higher than the buying price. 
* If it is bearish, you do not need to answer question 2.3.4.5
* The Recommended selling price should be the take-profit price when bullish. If the former is bearish, it can be skipped directly.

Answer according to the example format, do not explain
answer example format:
1. Will it be bullish or bearish in the next six months?: Bullish/Bearish
2. Recommended buying price, considering a margin of error of +/- 5%?: [a integer] NTD
3. Recommended selling price, assuming a stop-loss strategy with a maximum loss of 10%?: [a integer] NTD
4. Recommended holding period for this investment? (months): [a integer] months
5. Suggested stop-loss strategy? What would be your criteria for triggering a sell order?: [strategy]
'''
        }

        output_file = f'output_{stock_id}.txt'
        log_file = f'output_log_{stock_id}.txt'
        csv_file = f'output_{stock_id}.csv'
        fieldnames = ['Bullish/Bearish', 'Recommended buying price', 'Recommended selling price', 'Recommended holding period', 'Stop-loss strategy']

        # 將輸出存成txt檔案
        with open(output_file, 'w', encoding='utf-8') as f:
            async for part in await AsyncClient().chat(model='llama3:8b', messages=[message], stream=True, options={"temperature": 0.9}):
                f.write(part['message']['content'])

        # 解析輸出結果
        with open(output_file, 'r', encoding='utf-8') as f:
            output = f.read()
            parsed_result = parse_output(output)

        # 將結果寫入CSV檔案
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

        # 保存歷史紀錄到 log 檔案
        with open(log_file, 'a', encoding='utf-8') as log_f:
            log_f.write(f'no.{_} === {datetime.datetime.now()} ===\n')
            log_f.write(output)
            log_f.write('\n\n')

        # 輸出結果到終端
        print(parsed_result)

asyncio.run(chat())
