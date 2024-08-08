from supabase import create_client, Client
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 定义要爬取的股票ID和关键词
stocks = [
    {"stock_id": "2330", "keyword": "台積電"},
    {"stock_id": "3443", "keyword": "創意"},
    {"stock_id": "2002", "keyword": "中鋼"},
    {"stock_id": "2317", "keyword": "鴻海"},
    {"stock_id": "2731", "keyword": "雄獅"},
]

# 计算日期范围
end_date = datetime.today()
start_date = end_date - timedelta(days=90)

for stock in stocks:
    stock_id = stock["stock_id"]

    # 从 Supabase 读取新闻数据
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
        continue  # 跳过当前股票ID，继续处理下一个

    # 将日期列转换为 datetime 类型
    news["date"] = pd.to_datetime(news["date"])

    # 过滤数据，只包含过去90天内的行
    recent_news = news[(news["date"] >= start_date) & (news["date"] <= end_date)]

    # 计算 arousal 列的总和和总数
    total_arousal = recent_news["arousal"].sum()
    count = len(recent_news)

    if count > 0:
        # 计算三个月的平均 arousal
        mean_arousal = total_arousal / count
    else:
        mean_arousal = 0

    # 将处理后的数据插入到新的表 "score_mean"
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
