import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
import random
from selenium.webdriver.chrome.options import Options

# 設置 Chrome driver 的選項
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--headless")

# 加载环境变量
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 全局 WebDriver 單例
driver_instance = None

def get_driver():
    global driver_instance
    if driver_instance is None:
        driver_instance = webdriver.Chrome(options=options)
    return driver_instance

def quit_driver():
    global driver_instance
    if driver_instance:
        driver_instance.quit()
        driver_instance = None

def insert_news_to_supabase(stock_id, headline):
    """Insert the news headline into Supabase, if not exists"""
    today = datetime.today().strftime('%Y-%m-%d')

    try:
        response = supabase.table('news_content') \
            .select('*') \
            .eq('stockID', stock_id) \
            .eq('date', today) \
            .eq('content', headline) \
            .execute()

        if response.data:
            print(f"Duplicate news found, not inserting: {headline}")
            return

        supabase.table('news_content').insert({
            'stockID': stock_id,
            'date': today,
            'content': headline,
            'gemini_signal': None,
            'emotion': None,
            'arousal': None
        }).execute()
        print(f"News inserted: {headline}")

    except Exception as e:
        print(f"Error inserting news into Supabase: {e}")

def get_stock_name(stock_id):
    """Fetch stock name from Supabase using stock ID"""
    try:
        response = supabase.table('stock').select('stock_name').eq('stockID', stock_id).execute()
        stock_name = response.data[0]['stock_name'] if response.data else None
        return stock_name
    except Exception as e:
        print(f"Error fetching stock name for {stock_id}: {e}")
        return None

def format_news_item(headline, link):
    """格式化新聞項目為統一字典結構"""
    return {"headline": headline, "link": link}

def fetch_news_ltn(stock_id, stock_name):  
    """Fetch news from Liberty Times Net for the given stock name and insert into Supabase"""
    today = datetime.today().strftime('%Y%m%d')
    news_list = []

    url = f'https://search.ltn.com.tw/list?keyword={stock_name}&sort=date&start_time={today}&end_time={today}&type=business'

    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_items = soup.find_all('div', class_='cont')

        for item in news_items[:3]:
            headline = item.find('a').text.strip()
            link = item.find('a')['href']
            news_list.append(format_news_item(headline, link))
            insert_news_to_supabase(stock_id, headline)

    except Exception as e:
        print(f"Error fetching news from LTN for {stock_name}: {e}")

    return news_list

def fetch_news_tvbs(stock_id, stock_name):
    """Fetch news from TVBS for the given stock ID and name and insert into Supabase"""
    today = datetime.today().strftime('%Y/%m/%d')
    news_list = []
    keyword = f'{stock_id}{stock_name}'
    encoded_keyword = quote(keyword)
    base_url = f"https://news.tvbs.com.tw/news/searchresult/{encoded_keyword}/news/"
    
    url = base_url + "1"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Error fetching page 1 for {stock_id} {stock_name}: {response.status_code}")
            return news_list

        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all('li')

        for e in elements:
            link_element = e.find('a')
            if not link_element:
                continue
            link = link_element['href']
            title_element = e.find('h2', class_='txt')
            headline = title_element.text.strip() if title_element else "No title"

            if headline == "No title":
                continue

            news_list.append(format_news_item(headline, link))
            insert_news_to_supabase(stock_id, headline)

            if len(news_list) >= 3:
                break

    except Exception as e:
        print(f"Error fetching news from TVBS for {stock_id} {stock_name}: {e}")

    return news_list

def fetch_news_cnye(stock_id, stock_name):
    """Fetch news from CNYE for the given stock name"""
    url = f"https://www.cnyes.com/search/news?keyword={stock_name}"
    
    driver = get_driver()
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "jsx-1986041679") and contains(@class, "news")]'))
        )

        elements = driver.find_elements(By.XPATH, '//a[contains(@class, "jsx-1986041679") and contains(@class, "news")]')

        news_list = []
        for e in elements[:3]:
            href = e.get_attribute("href")
            headline = e.text.strip()
            news_list.append(format_news_item(headline, href))
            insert_news_to_supabase(stock_id, headline)

        return news_list

    except Exception as e:
        print(f"Error fetching news from CNYE: {e}")
        return []
    
def fetch_news_chinatime(stock_id, stock_name):
    """Fetch news from Chinatime for the given stock name"""
    keyword = f'{stock_id}{stock_name}'
    encoded_keyword = quote(keyword)
    base_url = f"https://www.chinatimes.com/search/{encoded_keyword}?page="

    news_list = []

    driver = get_driver()
    try:
        for i in range(1, 4):
            url = base_url + str(i) + "&chdtv"
            driver.get(url)
            time.sleep(random.uniform(3, 6))

            try:
                article_list = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "article-list"))
                )
            except:
                print(f"Error: Article list not found on page {i}.")
                break

            articles = article_list.find_elements(By.TAG_NAME, "li")

            if not articles:
                print(f"No articles found on page {i}. Stopping crawl.")
                break

            for article in articles:
                try:
                    title_elements = article.find_elements(By.TAG_NAME, "h3")
                    if title_elements:
                        title_text = title_elements[0].text
                    else:
                        continue

                    link_element = article.find_element(By.TAG_NAME, "a")
                    link_url = link_element.get_attribute("href")

                    news_list.append(format_news_item(title_text, link_url))
                    insert_news_to_supabase(stock_id, title_text)

                    if len(news_list) >= 3:
                        return news_list

                except Exception as e:
                    print(f"Error extracting article on page {i}: {e}")
    except Exception as e:
        print(f"Error accessing Chinatime: {e}")

    return news_list

def print_news(news_list, source):
    """以統一格式輸出新聞標題和連結"""
    if news_list:
        print(f"\nNews from {source}:")
        for news in news_list:
            print(f"title: {news['headline']}\nlink: {news['link']}\n")
    else:
        print(f"No news available from {source}.")

def main():
    stock_id = input("Enter the stock ID: ")
    stock_name = get_stock_name(stock_id)

    if stock_name:
        print(f"\nFetching news for {stock_id} {stock_name}...\n")
        news_ltn = fetch_news_ltn(stock_id,stock_name)
        news_tvbs = fetch_news_tvbs(stock_id, stock_name)
        news_cnye = fetch_news_cnye(stock_id,stock_name)
        news_chinatime = fetch_news_chinatime(stock_id, stock_name)
        print_news(news_ltn, "Liberty Times Net (LTN)")
        print_news(news_tvbs, "TVBS")
        print_news(news_cnye, "CNYE")
        print_news(news_chinatime, "Chinatime")
    else:
        print("Stock name not found in database.")

if __name__ == "__main__":
    main()
    quit_driver()
