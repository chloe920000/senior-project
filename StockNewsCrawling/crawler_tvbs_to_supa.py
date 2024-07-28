import time
import os
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 爬取新闻数据
stock_id = '2330'
glob_url = 'https://news.tvbs.com.tw/news/searchresult/台積電/news/'

date_last = ''

for i in range(2):
    # 请求网页内容
    url = glob_url + str(i+1)
    response = requests.get(url)
    
    # 解析网页内容
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 找到所有的 <li> 元素
    elements = soup.find_all('li')
    
    # 提取每个元素的文字内容
    for e in elements:
        try:
            # 找到时间元素
            time_element = e.find('div', class_='time')
            if time_element is None:
                continue
            
            time_text = time_element.text.strip()
            time_datetime = datetime.strptime(time_text, '%Y/%m/%d %H:%M')
            formatted_date = time_datetime.strftime('%Y-%m-%d')
            
            # 每次循环开始时清空 content 变量
            content = ''
            
            # 找到摘要元素
            summary_element = e.find('div', class_='summary')
            if summary_element is None:
                continue
            
            # 拼接新闻内容
            content += summary_element.text.strip()
            
            # 打印爬取进度
            print(f'Date:{formatted_date}, link:{url}')

            # 将数据插入 Supabase
            record = {
                'stockID': int(stock_id),
                'date': formatted_date,
                'content': content
            }
            supabase.table('news_content').insert(record).execute()
            
        except Exception as ex:
            print("爬取失败", ex)
            print(f'link:{url}')
            pass
    time.sleep(1)
