import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
from ollama import AsyncClient
from get_prompt_data import *
from prompt_generater import *


date = '2023-01-01'
stock_id = '8305'
end_year = date[:4]
start_year = end_year - 4

# 載入環境變數
load_dotenv()
# 初始化 Supabase 客戶端
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 解析模型輸出結果
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
    
    # 取得prompt需要的股票資料
    result = select_supabase_data(stock_id, date)
    data_bps = result['data_bps']
    data_roe = result['data_roe']
    data_Share_capital = result['data_Share_capital']
    data_eps = result['data_eps']
    data_GM = result['data_GM']
    data_OPM = result['data_OPM']
    data_DBR = result['data_DBR']
    stock_price = result['stock_price']


    # Summarize historical stock data
    yearly_summary = summarize_stock_data('daily_price.csv', stock_id, end_year)
    summary_str = get_stock_summary_string(yearly_summary)

    # 取得公司背景資料
    company_background = get_company_background(stock_id)
    

    # 處理數據
    bps_values = [safe_get_value(data_bps, year, 'bps') for year in range(start_year, end_year + 1)]
    roe_values = [safe_get_value(data_roe, year, 'roe') for year in range(start_year, end_year + 1)]
    capital_values = [safe_get_value(data_Share_capital, year, 'share_capital') for year in range(start_year, end_year + 1)]
    #roa_values = [safe_get_value(data_roa, year, 'roa') for year in range(start_year, end_year + 1)]
    eps_values = [safe_get_value(data_eps, year, 'eps') for year in range(start_year, end_year + 1)]
    #per_values = [safe_get_value(data_per, year, 'per') for year in range(start_year, end_year + 1)]
    GM_values = [safe_get_value(data_GM, year, 'gm') for year in range(start_year, end_year + 1)]
    OPM_values = [safe_get_value(data_OPM, year, 'opm') for year in range(start_year, end_year + 1)]
    DBR_values = [safe_get_value(data_DBR, year, 'dbr') for year in range(start_year, end_year + 1)]
    
    # 把五年的資料變成字串格式
    bps_str = ', '.join(map(str, bps_values))
    roe_str = ', '.join(map(str, roe_values))
    capital_str = ', '.join(map(str, capital_values))
    #roa_str = ', '.join(map(str, roa_values))
    eps_str = ', '.join(map(str, eps_values))
    #per_str = ', '.join(map(str, per_values))
    GM_str = ', '.join(map(str, GM_values))
    OPM_str = ', '.join(map(str, OPM_values))
    DBR_str = ', '.join(map(str, DBR_values))

    print("bps_str:", bps_str)
    print("roe_str:", roe_str)
    print("capital_str:", capital_str)
    #print("roa_str:", roa_str)
    print("eps_str:", eps_str)
    #print("per_str:", per_str)
    print("GM_str:", GM_str)
    print("OPM_str:", OPM_str)
    print("DBR_str:", DBR_str)
    print("summary_str:", summary_str)
    print("current price:", get_stock_price(stock_id))
    print("company background:", company_background)
    # --------------------------------循環次數------------------------------------ #
    for _ in range(1): 
        stock_price = get_stock_price(stock_id)

        # 使用 generate_message_content 生成 message_content
        message_content = generate_message_content(stock_id, bps_str, capital_str, roe_str, eps_str, GM_str, OPM_str, DBR_str, summary_str, get_stock_price(stock_id), company_background)
        
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
            async for part in await AsyncClient().chat(model='llama3.1:latest', messages=[message], stream=True, options={"temperature": 0.3}):
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

