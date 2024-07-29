import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re
from supabase import create_client, Client

# Selenium 進行網頁瀏覽和滾動
stock_id = "1101"
url = "https://www.cnyes.com/search/news?keyword=台泥"
driver = webdriver.Chrome()
driver.get(url)
news_url_l = []

for i in range(2):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

    elements = driver.find_elements(
        By.XPATH, '//a[contains(@class, "jsx-1986041679") and contains(@class, "news")]'
    )
    for e in elements:
        href = e.get_attribute("href")
        if href not in news_url_l:  # 避免重複添加
            news_url_l.append(href)
            print("目標元素的網址:", href)

driver.quit()

# Supabase setup
url = "https://ifdyheuivlbmhsbpuyqf.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZHloZXVpdmxibWhzYnB1eXFmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyMTMxMTU2OSwiZXhwIjoyMDM2ODg3NTY5fQ.c6DehH3cUJrjHa22_ps0w32xCLRhS5AAQUqc1sHqoI0"
# 初始化 Supabase 客戶端
supabase: Client = create_client(url, key)

# Requests 和 BeautifulSoup 進行網頁解析
content = ""
date_last = ""
article = ""

for index, link in enumerate(news_url_l):
    try:
        response = requests.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # 找到時間元素 #2024-07-26 09:04
        time_text = soup.find("p", class_="alr4vq1").text.strip()
        match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", time_text)

        if match:
            time_string = match.group()
            time_datetime = datetime.strptime(time_string, "%Y-%m-%d %H:%M")
            formatted_date = time_datetime.strftime("%Y%m%d")
            supabase_date_format = time_datetime.strftime("%Y-%m-%d")

        print("supabase_date_format:", supabase_date_format)

        if date_last != formatted_date:
            article = ""
        date_last = formatted_date

        p = soup.find("main", class_="c1tt5pk2")
        contents = p.find_all("p")

        for content in contents:
            article += content.text.strip()

        # Write data to Supabase
        data = {
            "stockID": int(stock_id),
            "date": supabase_date_format,
            "content": article,
            "gemini_signal": None,  # Assuming this is to be filled later
            "emotion": None,  # Assuming this is to be filled later
            "arousal": None,
        }
        response = supabase.table("news_content").insert(data).execute()
        if response.data:
            print(
                f"[{index+1}/{len(news_url_l)}], Date:{formatted_date}, link:{link} - Inserted into Supabase"
            )
        else:
            print(f"Failed to insert into Supabase: {response.error}")

    except requests.exceptions.Timeout:
        print(f"Request timed out for link: {link}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed for link: {link}, Error: {e}")
    except Exception as e:
        print(f"爬取失敗 {e}")
        print("link", link)
    time.sleep(1)
