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


def scoreMean(dates, stocks):
    print("in scoreMean")
    """# 確保至少 stock_id 或 keyword 其中一個有值
    if not stock_id and not keyword:
        raise ValueError("At least one of stock_id or keyword must be provided.")

    # 如果只有 keyword 沒有 stock_id，從 Supabase 查詢 stockID
    if not stock_id and keyword:
        stock_response = (
            supabase.from_("stock")
            .select("stockID")
            .eq("stock_name", keyword)
            .execute()
        )
        stock_data = stock_response.data

        if not stock_data or len(stock_data) == 0:
            raise ValueError(f"No stockID found for keyword: {keyword}")

        # 獲取 stockID
        stock_id = stock_data[0]["stockID"]

    # 如果只有 stock_id 沒有 keyword，從 Supabase 查詢 stock_name
    if not keyword and stock_id:
        stock_response = (
            supabase.from_("stock")
            .select("stock_name")
            .eq("stockID", stock_id)
            .execute()
        )
        stock_data = stock_response.data

        if not stock_data or len(stock_data) == 0:
            raise ValueError(f"No keyword (stock_name) found for stockID: {stock_id}")

        # 獲取 stock_name
        keyword = stock_data[0]["stock_name"]

    stocks = [{"stock_id": stock_id, "keyword": keyword}]
    # 輸出 stocks 列表
    print("Stocks list:", stocks)

    # stocks 是包含 stock_id 和 keyword 的列表
    if not stocks:
        raise ValueError("Stocks list cannot be empty.")"""

    mean_data = []  # 用於儲存將要插入的字典列表

    # 逐個處理每個股票和日期
    for stock in stocks:
        stock_id = stock.get("stock_id")
        keyword = stock.get("stock_name")

        for date_str in dates:
            # 解析日期
            end_date = datetime.strptime(date_str, "%Y-%m-%d")
            start_date = end_date - timedelta(days=30)

            # 從 Supabase 讀取新聞數據
            news_response = (
                supabase.table("news_test")
                .select("*")
                .eq("stockID", stock_id)
                .execute()
            )

            if news_response.data:
                news_data = news_response.data
                news = pd.DataFrame(news_data)
            else:
                print(
                    f"Failed to fetch data from Supabase for stock_id {stock_id}: data={news_response.data}, count={news_response.count}"
                )
                continue  # 跳過該股票ID，繼續處理下一個

            # 將日期列轉換為 datetime 類型
            news["date"] = pd.to_datetime(news["date"])

            # 過濾數據，只包含過去30天內的行
            recent_news = news[
                (news["date"] >= start_date) & (news["date"] <= end_date)
            ]

            # 計算 arousal 列的總和和總數
            total_arousal = recent_news["arousal"].sum()
            news_count = len(recent_news)

            if news_count > 0:
                # 計算過去30天的平均 arousal
                mean_arousal = total_arousal / news_count
            else:
                mean_arousal = 0

            # 准备插入的数据
            insert_data = {
                "date": end_date.strftime("%Y-%m-%d"),
                "arousal_mean": mean_arousal,
                "stockID": stock_id,
                "count": news_count,
            }
            # 將準備好的字典添加到插入數據列表
            mean_data.append(insert_data)

            # 將處理后的數據插入到新的表 "score_mean"
            insert_response = supabase.table("score_mean").insert(insert_data).execute()

            if insert_response.data is None:
                print(
                    f"Failed to insert data for stock_id {stock_id}: {insert_response}"
                )
                raise Exception("Data insertion failed")

        print(f"Data for stock_id {stock_id} processed and inserted successfully.")

    # 返回將要插入的字典列表
    return mean_data


"""
# test
if __name__ == "__main__":
    # Define test dates and stock
    test_dates = ["2024-07-30"]

    # 測試传入股票的 stocks 列表格式
    test_stocks = [{"stock_id": "2330", "stock_name": "台積電"}]
    try:
        print("Testing with keyword '台積電'...")
        mean_result = scoreMean(test_dates, test_stocks)
        print("Inserted data:", mean_result)
    except Exception as e:
        print(f"Error testing with keyword '台積電': {e}")
"""
