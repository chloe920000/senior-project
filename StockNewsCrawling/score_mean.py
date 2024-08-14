from supabase import create_client, Client
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 定義要爬取的股票ID和關鍵詞
stocks = [
    {"stock_id": "2330", "keyword": "台積電"},
    {"stock_id": "3443", "keyword": "創意"},
    {"stock_id": "2002", "keyword": "中鋼"},
    {"stock_id": "2317", "keyword": "鴻海"},
    {"stock_id": "2731", "keyword": "雄獅"},
]

# 計算日期範圍
end_date = datetime.today()
start_date = end_date - timedelta(days=90)

for stock in stocks:
    stock_id = stock["stock_id"]

    # 從 Supabase 讀取新聞數據
    news_response = (
        supabase.table("news_test").select("*").eq("stockID", stock_id).execute()
    )
    if news_response.data:
        news_data = news_response.data
        news = pd.DataFrame(news_data)
    else:
        print(
            f"Failed to fetch data from Supabase for stock_id {stock_id}: data={news_response.data}, count={news_response.count}"
        )
        continue  # 跳過前股票ID，繼續處理下一個

    # 將日期列轉換為 datetime 類型
    news["date"] = pd.to_datetime(news["date"])

    # 過濾數據，只包含過去90天内的行
    recent_news = news[(news["date"] >= start_date) & (news["date"] <= end_date)]

    # 計算 arousal 列的總和和總數
    total_arousal = recent_news["arousal"].sum()
    count = len(recent_news)

    if count > 0:
        # 計算三個月的平均 arousal
        mean_arousal = total_arousal / count
    else:
        mean_arousal = 0

    # 將處理后的數據插入到新的表 "score_mean"
    insert_response = (
        supabase.table("score_mean")
        .insert(
            {
                "date": end_date.strftime(
                    "%Y-%m-%d"
                ),  # 使用 strftime 将日期转换为字符串
                "arousal_mean": mean_arousal,
                "stockID": stock_id,
                "count": count,
            }
        )
        .execute()
    )
    if insert_response.data is None:
        print(f"Failed to insert data for stock_id {stock_id}: {insert_response}")
        raise Exception("Data insertion failed")

    print(f"Data for stock_id {stock_id} processed and inserted successfully.")
