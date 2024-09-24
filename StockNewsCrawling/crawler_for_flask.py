import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import time

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
    """Fetch news from Liberty Times Net for the given stock name"""
    today = datetime.today().strftime('%Y%m%d')
    news_list = []
    url = f'https://search.ltn.com.tw/list?keyword={stock_name}&start_time={today}&end_time={today}&sort=date&type=all&page=1'

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
            print(f"No news found for {stock_name} on {today}.")
    except Exception as e:
        print(f"Error fetching news from ltn for {stock_name}: {e}")

    return news_list

def fetch_news_tvbs(stock_name):
    """Fetch news from TVBS for the given stock name"""
    today = datetime.today().strftime('%Y/%m/%d')
    news_list = []
    glob_url = f"https://news.tvbs.com.tw/news/searchresult/{stock_name}/news/"
    page = 1
    add_page = 2
    
    while True:
        url = glob_url + str(page)
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.find_all('li')
            news_found = False

            for e in elements:
                time_element = e.find("div", class_="time")
                if not time_element:
                    continue

                time_text = time_element.text.strip()
                time_datetime = datetime.strptime(time_text, "%Y/%m/%d %H:%M")
                formatted_date = time_datetime.strftime("%Y-%m-%d")

                if formatted_date == today:
                    headline = e.find("div", class_="summary").text.strip() if e.find("div", class_="summary") else "No title"
                    link = url
                    news_list.append({"headline": headline, "link": link})
                    news_found = True
                else:
                    break

            if not news_found:
                break

            page += add_page
            time.sleep(2)

        except Exception as e:
            print(f"Error fetching news from TVBS for {stock_name}: {e}")
            break

    return news_list

def print_news(news_list, source):
    """Print the headlines and links from the given source"""
    if news_list:
        print(f"\nNews from {source}:")
        for news in news_list:
            
            print(f"Headline: {news['headline']}")
            print(f"Link: {news['link']}\n")
    else:
        print(f"No news available from {source}.")

def main():
    stock_id = input("Enter the stock ID: ")
    stock_name = get_stock_name(stock_id)

    if stock_name:
        print(f"\nFetching news for {stock_name}...\n")
        news_ltn = fetch_news_ltn(stock_name)
        news_tvbs = fetch_news_tvbs(stock_name)
        
        print_news(news_ltn, "Liberty Times Net (ltn)")
        print_news(news_tvbs, "TVBS")

    else:
        print("Stock name not found in Supabase.")

if __name__ == "__main__":
    main()
