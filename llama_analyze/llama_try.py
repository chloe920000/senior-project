
import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv
import datetime
import os
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
        if soup.select('#main-0-QuoteHeader-Proxy')[0].select('.C($c-trend-down)')[0]:
            status = '-'
    except:
        try:
            if soup.select('#main-0-QuoteHeader-Proxy')[0].select('.C($c-trend-up)')[0]:
                status = '+'
        except:
            status = '▬'

    return f'{title} : {current_price} ( {status}{change} )'  # Return the formatted string

def get_company_background(stock_id):
    url = f'https://tw.stock.yahoo.com/quote/{stock_id}/profile'
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    
    # 查找第一個 section
    first_section = soup.find('section')
    
    # 查找第一個 section 中的最後一個 div
    if first_section:
        background_div = first_section.find_all('div')[-1]
        if background_div:
            return background_div.get_text().strip()
    
    return '無法取得公司背景資料'





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


def summarize_stock_data(file_path, stock_id, end_year):
    data = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    # 過濾出指定年份及之前的資料
    data = data[data.index.year <= end_year]
    yearly_summary = data.resample('Y').agg({
        stock_id: ['first', 'last', 'max', 'min']
    })
    yearly_summary.columns = ['Open', 'Close', 'High', 'Low']
    return yearly_summary


def get_stock_summary_string(summary):
    summary_str = "\n".join([f"{year.strftime('%Y')}: Open={row['Open']}, Close={row['Close']}, High={row['High']}, Low={row['Low']}" 
                             for year, row in summary.iterrows()])
    return summary_str



"""
# BPS (book value per share) over last 5 years: 最近五年的每股淨值
# 每股淨值是指公司股東權益（即公司的淨資產）除以已發行股票的數量，表示每股股票所對應的公司淨資產價值

# Capital over last 5 years: 最近五年的資本
# 資本指的是公司用來營運和發展的資金，包括股本和債務資金

# ROE (return on equity) over last 5 years: 最近五年的股東權益報酬率
# 股東權益報酬率是指公司淨利潤除以股東權益，反映公司利用股東投入資金獲得利潤的能力

# ROA (return on assets) over last 5 years: 最近五年的資產報酬率
# 資產報酬率是指公司淨利潤除以總資產，反映公司利用其資產獲得利潤的能力

# EPS (earnings per share) over last 5 years: 最近五年的每股盈餘
# 每股盈餘是指公司淨利潤除以已發行股票數量，表示每股股票所能獲得的利潤

# PER (price earnings ratio) over last 5 years: 最近五年的本益比
# 本益比是指股票價格除以每股盈餘，反映市場對公司未來盈利能力的預期

# Reference historical prices: 參考歷史價格
# 歷史價格是指股票在過去某段時間內的交易價格數據

# Current price: 當前價格
# 當前價格是指股票目前在市場上的交易價格

"""


async def chat():
    stock_id = '2002'
    end_year = 2023
    # 使用過去五年的資料
    start_year = end_year - 4
    
    # 讀取CSV檔案並設置索引列為字符串
    data_bps = pd.read_csv('year_bps.csv', index_col='year', dtype={'year': str})
    data_roe = pd.read_csv('year_roe.csv', index_col='year', dtype={'year': str})
    data_Share_capital = pd.read_csv('year_Share_capital.csv', index_col='year', dtype={'year': str})
    data_roa = pd.read_csv('year_roa.csv', index_col='year', dtype={'year': str})  # 新增讀取ROA的資料
    data_eps = pd.read_csv('year_eps.csv', index_col=f'Year_{stock_id}', dtype={f'Year_{stock_id}': str})  # 新增讀取EPS的資料
    data_per = pd.read_csv('year_per.csv', index_col='year', dtype={'year': str})  # 新增讀取PER的資料
    #2024/7/15 新增毛利率GM 營益率OPM 負債比率DBR
    data_GM = pd.read_csv('year_GM.csv', index_col='year', dtype={'year': str})
    data_OPM = pd.read_csv('year_OPM.csv', index_col='year', dtype={'year': str})
    data_DBR = pd.read_csv('year_DBR.csv', index_col='year', dtype={'year': str})
    
    # Summarize historical stock data
    yearly_summary = summarize_stock_data('daily_price.csv', stock_id, end_year)
    summary_str = get_stock_summary_string(yearly_summary)

    # 取得公司背景資料
    company_background = get_company_background(stock_id)
    
    def safe_get_value(data, year, stock_id):
        try:
            return data.loc[str(year), str(stock_id)]
        except KeyError:
            return 'NA'

    bps_values = [safe_get_value(data_bps, year, stock_id) for year in range(start_year, end_year + 1)]
    roe_values = [safe_get_value(data_roe, year, stock_id) for year in range(start_year, end_year + 1)]
    capital_values = [safe_get_value(data_Share_capital, year, stock_id) for year in range(start_year, end_year + 1)]
    roa_values = [safe_get_value(data_roa, year, stock_id) for year in range(start_year, end_year + 1)]
    eps_values = [safe_get_value(data_eps, year, stock_id) for year in range(start_year, end_year + 1)]
    per_values = [safe_get_value(data_per, year, stock_id) for year in range(start_year, end_year + 1)]
    GM_values = [safe_get_value(data_GM, year, stock_id) for year in range(start_year, end_year + 1)]
    OPM_values = [safe_get_value(data_OPM, year, stock_id) for year in range(start_year, end_year + 1)]
    DBR_values = [safe_get_value(data_DBR, year, stock_id) for year in range(start_year, end_year + 1)]
    
    # 把五年的資料變成字串格式
    bps_str = ', '.join(map(str, bps_values))
    roe_str = ', '.join(map(str, roe_values))
    capital_str = ', '.join(map(str, capital_values))
    roa_str = ', '.join(map(str, roa_values))
    eps_str = ', '.join(map(str, eps_values))
    per_str = ', '.join(map(str, per_values))
    GM_str = ', '.join(map(str, GM_values))
    OPM_str = ', '.join(map(str, OPM_values))
    DBR_str = ', '.join(map(str, DBR_values))

    print("bps_str:", bps_str)
    print("roe_str:", roe_str)
    print("capital_str:", capital_str)
    print("roa_str:", roa_str)
    print("eps_str:", eps_str)
    print("per_str:", per_str)
    print("GM_str:", GM_str)
    print("OPM_str:", OPM_str)
    print("DBR_str:", DBR_str)
    print("summary_str:", summary_str)
    print("current price:", get_stock_price(stock_id))
    print("company background:", company_background)
    # --------------------------------循環次數------------------------------------ #
    for _ in range(1): 
        stock_price = get_stock_price(stock_id)

        message_content = f'''Evaluate the stock price of TWSE{stock_id} based on the following data:

* BPS (book value per share) over last 5 years: {bps_str}
* Capital over last 5 years: {capital_str} * 100 million
* ROE (return on equity) over last 5 years: {roe_str}%
* ROA (return on assets) over last 5 years: {roa_str}%
* EPS (earnings per share) over last 5 years: {eps_str}
* PER (price earnings ratio) over last 5 years: {per_str}%
* GM (gross margin) over last 5 years: {GM_str}%
* OPM (operating profit margin) over last 5 years: {OPM_str}%
* DBR (debt-to-assets ratio) over last 5 years: {DBR_str}%
* Reference historical prices:
{summary_str}
* Current price: {stock_price}

Provide additional context about the company, industry, and market trends.

* Company Background:
{company_background}

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
        
        # 保存每次的input message到log檔案
        input_log_path = os.path.join('result_data', f'input_log_{stock_id}.txt')
        with open(input_log_path, 'a', encoding='utf-8') as input_log_f:
            input_log_f.write(f'no.{_} === {datetime.datetime.now()} ===\n')
            input_log_f.write(message_content)
            input_log_f.write('\n\n')

        message = {
            'role': 'user',
            'content': message_content
        }

        # 修改路徑
        result_path = os.path.join('result_data', stock_id, f'output_{stock_id}.txt')
        log_path = os.path.join('result_data', stock_id, f'output_log_{stock_id}.txt')
        csv_path = os.path.join('result_data', stock_id, f'output_{stock_id}.csv')

        # 確保目錄存在
        os.makedirs(os.path.dirname(result_path), exist_ok=True)

        fieldnames = ['Bullish/Bearish', 'Recommended buying price', 'Recommended selling price', 'Recommended holding period', 'Stop-loss strategy']

        # 將輸出存成txt檔案
        with open(result_path, 'w', encoding='utf-8') as f:
            async for part in await AsyncClient().chat(model='llama3:8b', messages=[message], stream=True, options={"temperature": 0.3}):
                f.write(part['message']['content'])

        # 解析輸出結果
        with open(result_path, 'r', encoding='utf-8') as f:
            output = f.read()
            parsed_result = parse_output(output)

        # 將結果寫入CSV檔案
        # 檢查CSV檔案是否存在
        try:
            with open(csv_path, 'x', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        except FileExistsError:
            pass

        # 將解析結果寫入CSV檔案
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(parsed_result)

        # 保存歷史紀錄到 log 檔案
        with open(log_path, 'a', encoding='utf-8') as log_f:
            log_f.write(f'no.{_} === {datetime.datetime.now()} ===\n')
            log_f.write(output)
            log_f.write('\n\n')

        # 輸出結果到終端
        print(_)
        print(parsed_result)

asyncio.run(chat())

