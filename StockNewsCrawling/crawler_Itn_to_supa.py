import time
import os
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 爬取新闻数据
stock_id = "2330"
global_url = 'https://search.ltn.com.tw/list?keyword=台積電&start_time=20221201&end_time=20240402&sort=date&type=all&page='

page = 1
news_url_l = []

for i in range(2):
    url =  global_url + str(i+1)
    
    # 创建 WebDriver 实例
    driver = webdriver.Chrome()
    
    # 设置隐式等待时间
    driver.implicitly_wait(10) # seconds
    
    # 载入网页
    driver.get(url)
    
    try:
        # 使用显式等待，等待特定元素出现
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "cont")]'))
        )
        
        # 获取所有元素
        elements = driver.find_elements(By.XPATH, '//div[contains(@class, "cont")]')
        
        for e in elements:
            # 获取该元素的 href 属性
            href = e.get_attribute('href')
            if href:
                print("目标元素的网址:", href)
                news_url_l.append(href)
                
    except TimeoutException:
        print("网页载入超时，重新载入...")
        # 关闭当前的 WebDriver 实例
        driver.quit()
        continue
    
    # 关闭 WebDriver 实例
    driver.quit()

# 找到所有自由财经的网址
news_url_l2 = [href for href in news_url_l if href.startswith("https://ec")]
news_url_l2 = news_url_l2[:]

# 爬取详细新闻内容并存储到 Supabase
date_last = ''
article = ''

for index, link in enumerate(news_url_l2):
    # 请求网页内容
    response = requests.get(link)
    # 解析网页内容
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        time_element = soup.find_all('span', class_='time')
        time_text = time_element[1].text.strip()
        time_datetime = datetime.strptime(time_text, '%Y/%m/%d %H:%M')
        formatted_date = time_datetime.strftime('%Y-%m-%d')
        
        if date_last != formatted_date:
            article = ''
        date_last = formatted_date
        
        # 每次循环开始时清空 article 变量
        article = ''
        
        p = soup.find_all('div', class_="text")[1]
        contents = p.find_all('p')
        
        for content in contents:
            article = article + content.text.strip()
            
        # 打印爬取进度
        print(f'[{index+1}/{len(news_url_l2)}], Date:{formatted_date}, link:{link}')

        # 将数据插入 Supabase
        record = {
            'stockID': int(stock_id),
            'date': formatted_date,
            'content': article
        }
        supabase.table('news_content').insert(record).execute()
            
    except Exception as e:
        print("爬取失败", e)
        print(f'[{index+1}/{len(news_url_l2)}], Date:{formatted_date}, link:{link}')
        pass
    time.sleep(1)
