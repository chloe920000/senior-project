#獲取所有prompt需要的股市資料
import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
from ollama import AsyncClient

# 載入環境變數
load_dotenv()
# 初始化 Supabase 客戶端
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
# 获取公司背景资料
def get_company_background(stock_id):
    url = f'https://tw.stock.yahoo.com/quote/{stock_id}/profile'
    web = requests.get(url)
    soup = BeautifulSoup(web.text, "html.parser")
    
    # 查找第一个 section
    first_section = soup.find('section')
    
    # 查找第一个 section 中的最后一个 div
    if first_section:
        background_div = first_section.find_all('div')[-1]
        if background_div:
            return background_div.get_text().strip()
    
    return '无法取得公司背景资料'

# 汇总股票数据
def summarize_stock_data(file_path, stock_id, end_year):
    data = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    # 过滤出指定年份及之前的数据
    data = data[data.index.year <= end_year]
    yearly_summary = data.resample('Y').agg({
        stock_id: ['first', 'last', 'max', 'min']
    })
    yearly_summary.columns = ['Open', 'Close', 'High', 'Low']
    return yearly_summary

# 將彙總資料轉換為string格式
def get_stock_summary_string(summary):
    summary_str = "\n".join([f"{year.strftime('%Y')}: Open={row['Open']}, Close={row['Close']}, High={row['High']}, Low={row['Low']}" 
                             for year, row in summary.iterrows()])
    return summary_str

#確保資料安全取值
def safe_get_value(data, year, column_name):
        try:
            value = data.loc[year, column_name]
            print(f"Retrieved {column_name} for year {year}: {value}")
            if column_name == 'share_capital':
                return str(value)  # 對於 capital_value，返回字符串
            else:
                return float(value)  # 對於其他指標，返回浮點數
        except KeyError:
            print(f"KeyError: Unable to find {column_name} data for year {year}")
            return 'NA'
        except ValueError:
            print(f"ValueError: Unable to convert {column_name} data for year {year}")
            return 'NA'

# supabase資料存取
def select_supabase_data(stock_id, date):


    end_year = date[:4]
    # 使用過去五年的資料
    start_year = end_year - 4
    date_obj = datetime.strptime(date, '%Y-%m-%d')

    # 從 Supabase 獲取資料
    data_bps = get_data_from_supabase('year_bps', int(stock_id), int(start_year), int(end_year))
    data_roe = get_data_from_supabase('year_roe', int(stock_id), int(start_year), int(end_year))
    data_Share_capital = get_data_from_supabase('year_share_capital', int(stock_id), int(start_year), int(end_year))
    #data_roa = get_data_from_supabase('year_roa', int(stock_id), int(start_year), int(end_year))
    data_eps = get_data_from_supabase('year_eps', int(stock_id), int(start_year), int(end_year))
    #data_per = get_data_from_supabase('year_per', int(stock_id), int(start_year), int(end_year))
    data_GM = get_data_from_supabase('year_gm', int(stock_id), int(start_year), int(end_year))
    data_OPM = get_data_from_supabase('year_opm', int(stock_id), int(start_year), int(end_year))
    data_DBR = get_data_from_supabase('year_dbr', int(stock_id), int(start_year), int(end_year))
    
    stock_price = get_stock_price(stock_id, date)
    
    # 返回所有数据作为字典
    return {
        'data_bps': data_bps,
        'data_roe': data_roe,
        'data_Share_capital': data_Share_capital,
        'data_eps': data_eps,
        'data_GM': data_GM,
        'data_OPM': data_OPM,
        'data_DBR': data_DBR,
        'stock_price': stock_price
    }

def get_data_from_supabase(table_name, stock_id, start_year, end_year):
    print(f"Fetching data from table: {table_name}")
    response = supabase.table(table_name).select("*") \
        .eq('stockID', stock_id) \
        .gte('year', start_year) \
        .lte('year', end_year) \
        .execute()
    
    print(f"Response data: {response.data}")
    df = pd.DataFrame(response.data)
    if df.empty:
        print(f"No data found for {table_name}")
    else:
        print(f"Data fetched for {table_name}: {df}")
    df.set_index('year', inplace=True)
    return df

def get_stock_price(stock_id, date):
    # 读取 CSV 文件
    df = pd.read_csv('daily_price.csv')

    # 确保 'Date' 列被解析为日期格式
    df['Date'] = pd.to_datetime(df['Date'])

    # 将输入的日期字符串转换为 datetime 对象
    date_obj = pd.to_datetime(date)

    # 过滤条件：date = 给定日期 且 id = 给定 stock_id
    filtered_df = df[(df['Date'] == date_obj) & (df['id'] == stock_id)]

    # 如果找到匹配项，返回价格，否则返回 None 或一个合适的默认值
    if not filtered_df.empty:
        # 假设价格存储在 'Price' 列中
        price = filtered_df['Price'].iloc[0]
        return price
    else:
        return None