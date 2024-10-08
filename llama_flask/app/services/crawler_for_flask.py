import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait  # 新增
from selenium.webdriver.support import expected_conditions as EC  # 新增
from urllib.parse import quote
import random  # 新增，用於隨機延遲
from selenium.webdriver.chrome.options import Options  # 新增，用於防偵測設置
# 設置 Chrome driver 的選項
options = Options()
options.add_argument("--disable-gpu")  # 禁用 GPU 加速
options.add_argument("--headless")  # 啟用無頭模式
# 加载环境变量
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_stock_name(stock_id):
    """Fetch stock name from Supabase using stock ID"""
    try:
        response = supabase.table('stock').select('stock_name').eq('stockID', stock_id).execute()
        stock_name = response.data[0]['stock_name'] if response.data else None
        return stock_name
    except Exception as e:
        print(f"Error fetching stock name for {stock_id}: {e}")
        return None

def fetch_news_ltn(stock_name):
    """Fetch news from Liberty Times Net for the given stock ID and name"""
    today = datetime.today().strftime('%Y%m%d')
    news_list = []

    url = furl = f'https://search.ltn.com.tw/list?keyword={stock_name}&sort=date&start_time={today}&end_time={today}&type=business'

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        news_items = soup.find_all('div', class_='cont')

        if news_items:
            for item in news_items:
                headline = item.find('a').text.strip()
                link = item.find('a')['href']
                news_list.append({"headline": headline, "link": link})

        else:
            print(f"No news found for  {stock_name} on {today}.")
    except Exception as e:
        print(f"Error fetching news from LTN for  {stock_name}: {e}")

    return news_list[:3]  # 只返回前三條新聞

def fetch_news_tvbs(stock_id, stock_name):
    """Fetch news from TVBS for the given stock ID and name"""
    today = datetime.today().strftime('%Y/%m/%d')
    news_list = []
    keyword = f'{stock_id}{stock_name}'
    encoded_keyword = quote(keyword)
    base_url = f"https://news.tvbs.com.tw/news/searchresult/{encoded_keyword}/news/"
    
    url = base_url + "1"  # 只抓取第一頁
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching page 1 for {stock_id} {stock_name}: {response.status_code}")
            return news_list

        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all('li')  # 針對每個 li 進行處理

        for e in elements:
            # 找到連結和標題
            link_element = e.find('a')
            if not link_element:
                continue
            link = link_element['href']
            
            title_element = e.find('h2', class_='txt')
            headline = title_element.text.strip() if title_element else "No title"
            
            # 過濾掉 "No title" 的新聞
            if headline == "No title":
                continue
            
            # 將新聞信息儲存到列表中
            news_list.append({"headline": headline, "link": link})

            # 只取前三條新聞
            if len(news_list) >= 3:
                break
            
            # 每成功抓取一條新聞即時輸出
            print(f"Fetched: {headline}, Link: {link}")

        # 爬取完一頁新聞，顯示進度
        print(f"Finished fetching first page for {stock_id} {stock_name}")

    except Exception as e:
        print(f"Error fetching news from TVBS for {stock_id} {stock_name}: {e}")

    return news_list  # 返回前三條新聞

def fetch_news_cnye(stock_name):
    """Fetch news from CNYE for the given stock name"""
    url = f"https://www.cnyes.com/search/news?keyword={stock_name}"
    
    # 初始化瀏覽器
    driver = webdriver.Chrome()
    driver.get(url)

    try:
        # 等待最多10秒，直到目標元素出現
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@class, "jsx-1986041679") and contains(@class, "news")]'))
        )

        # 獲取新聞標題和連結
        elements = driver.find_elements(By.XPATH, '//a[contains(@class, "jsx-1986041679") and contains(@class, "news")]')

        news_list = []
        for e in elements[:3]:  # 只取前三個新聞
            href = e.get_attribute("href")
            headline = e.text.strip()
            news_list.append({"headline": headline, "link": href})
            print(f"Fetched: {headline}, Link: {href}")

        return news_list  # 返回前三條新聞

    except Exception as e:
        print(f"Error fetching news from CNYE: {e}")
        return []
    
    finally:
        driver.quit()  # 確保瀏覽器關閉

# 修改 fetch_news_chinatime 中的部分代碼
def fetch_news_chinatime(stock_id,stock_name):
    """Fetch news from Chinatime for the given stock name"""
    # 將 stock_name 進行 URL 編碼
    keyword = f'{stock_id}{stock_name}'
    encoded_keyword = quote(keyword)
    base_url = f"https://www.chinatimes.com/search/{encoded_keyword}?page="

    # 儲存新聞標題和連結
    news_list = []

    # 設定 Chrome driver 的防偵測選項
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用自動化控制標誌
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36")  # 偽裝 User-Agent
    driver = webdriver.Chrome(options=options)

    try:
        for i in range(1, 4):  # 只爬取前3頁
            # 組成頁面的 URL
            url = base_url + str(i) + "&chdtv"
            driver.get(url)

            # 隨機延遲，避免被網站偵測為機器人
            time.sleep(random.uniform(3, 6))

            # 等待頁面上的文章列表加載完成
            try:
                article_list = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "article-list"))
                )
            except:
                print(f"Error: Article list not found on page {i}.")
                continue

            # 找到所有的文章項目
            articles = article_list.find_elements(By.TAG_NAME, "li")

            # 迭代每篇文章，提取標題和連結
            for article in articles:
                try:
                    # 嘗試找到標題元素
                    title_elements = article.find_elements(By.TAG_NAME, "h3")
                    if title_elements:
                        title_text = title_elements[0].text
                    else:
                        print(f"No <h3> element found for article on page {i}. Skipping...")
                        continue  # 如果沒有找到標題，跳過這篇文章

                    # 提取連結
                    link_element = article.find_element(By.TAG_NAME, "a")
                    link_url = link_element.get_attribute("href")

                    # 將結果儲存到 news_list
                    news_list.append({
                        "headline": title_text,  # 使用 'headline' 作為統一鍵名
                        "link": link_url
                    })

                    # 每成功抓取一條新聞即時輸出
                    print(f"Fetched: {title_text}, Link: {link_url}")

                    # 若已經抓到 3 條新聞，則結束抓取
                    if len(news_list) >= 3:
                        driver.quit()  # 關閉瀏覽器
                        return news_list

                except Exception as e:
                    print(f"Error extracting article on page {i}: {e}")
    except Exception as e:
        print(f"Error accessing Chinatime: {e}")
    finally:
        driver.quit()  # 關閉瀏覽器

    return news_list




def print_news(news_list, source):
    """以統一格式輸出新聞標題和連結"""
    if news_list:
        print(f"\nNews from {source}:")
        for news in news_list:
            # 以統一格式顯示
            print(f"title: {news['headline']}\nlink: {news['link']}\n")
    else:
        print(f"No news available from {source}.")




def main():
    stock_id = input("Enter the stock ID: ")
    stock_name = get_stock_name(stock_id)

    if stock_name:
        print(f"\nFetching news for {stock_id} {stock_name}...\n")
        news_ltn = fetch_news_ltn(stock_id)
        news_tvbs = fetch_news_tvbs(stock_id, stock_name)
        news_cnye = fetch_news_cnye(stock_name)
        news_chinatime = fetch_news_chinatime(stock_id,stock_name)
        print_news(news_ltn, "Liberty Times Net (LTN)")
        print_news(news_tvbs, "TVBS")
        print_news(news_cnye, "CNYE")
        print_news(news_chinatime, "Chinatime")
    else:
        print("Stock name not found in database.")

if __name__ == "__main__":
    main()
