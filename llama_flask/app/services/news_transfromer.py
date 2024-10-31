import asyncio
from transformers import BertTokenizer, BertForSequenceClassification, pipeline
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 加載 .env 文件，確保 SUPABASE_URL 和 SUPABASE_KEY 被正確讀取
load_dotenv()

# 配置情緒分析模型 (使用 nlptown/bert-base-multilingual-uncased-sentiment 模型)
model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
model = BertForSequenceClassification.from_pretrained(model_name)
tokenizer = BertTokenizer.from_pretrained(model_name)

# 創建情緒分析 pipeline
sentiment_analyzer = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# Supabase 資訊
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# 統計數據存儲
emotion_counts = {"positive": 0, "neutral": 0, "negative": 0}
star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


async def analyze_and_store_sentiments(date, stocks):
    """
    分析並存儲距離指定日期前 30 天範圍內、指定股票的新聞情緒。
    date: string 日期 (格式: "YYYY-MM-DD")
    stocks: list 包含多個 stock_id 的列表
    """
    # 將 date 轉換為 datetime 格式
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)

    # 迭代 stocks 列表中的每個 stock_id
    for stock in stocks:
        stock_id = stock.get("stock_id")  # 確認 stock_id 取得方式

        # 從 news_test 表中提取距離指定日期前 30 天範圍內、指定 stock_id 的新聞
        response = (
            supabase.from_("news_test")
            .select("*")
            .gte("date", start_date)  # Filter for news on or after start_date
            .lte("date", end_date)  # Filter for news on or before end_date
            .eq("stockID", stock_id)  # 確認 stock_id 的篩選
            .execute()
        )
        news_data = response.data

        if not news_data:
            print(
                f"No news data found for stock_id {stock_id} within the specified date range."
            )
            continue

        # Initialize variables to calculate the average sentiment score
        total_sentiment_score = 0
        count = 0

        for news in news_data:
            try:
                print(f"Processing news ID: {news['id']} for stock_id: {stock_id}")

                # 進行情緒分析
                sentiment_result = bert_sentiment_analysis(news["content"])
                sentiment_score = sentiment_result["score"]
                star = sentiment_result["star"]
                emotion = sentiment_result["emotion"]

                # 累加情緒分數並增加計數
                total_sentiment_score += sentiment_score
                count += 1

                print(
                    f"Sentiment for news ID {news['id']}: {star} stars ({emotion}), Score: {sentiment_score}"
                )

                # 檢查該 news_id 是否已存在於 transformer_sentiment 表中
                existing_sentiment = (
                    supabase.from_("transformer_sentiment")
                    .select("id")
                    .eq("news_id", news["id"])
                    .execute()
                )

                # 如果該新聞已存在，則刪除舊記錄
                if existing_sentiment.data:
                    supabase.from_("transformer_sentiment").delete().eq(
                        "news_id", news["id"]
                    ).execute()
                    print(f"Deleted old sentiment analysis for news ID: {news['id']}")

                # 插入新的情緒分析結果
                insert_response = (
                    supabase.from_("transformer_sentiment")
                    .insert(
                        {
                            "news_id": news["id"],  # 將新聞的 id 傳入 news_id 欄位
                            "stockID": stock_id,  # 將 stock_id 傳入 stock_id 欄位
                            "sentiment": sentiment_score,  # 儲存置信度分數 (浮點數)
                            "star": star,  # 儲存星級 (1 到 5)
                            "emotion": emotion,  # 儲存情緒類型 (-1, 0, 1)
                        }
                    )
                    .execute()
                )

                # 使用 response.data 確認是否成功插入數據
                if insert_response.data:
                    print(f"Successfully inserted sentiment for news ID: {news['id']}")
                else:
                    print(
                        f"Failed to insert sentiment for news ID {news['id']}. Response: {insert_response}"
                    )

            except Exception as e:
                print(f"Failed to process news ID {news['id']}. Error: {str(e)}")

        # Calculate average sentiment score if count > 0
        if count > 0:
            average_sentiment = total_sentiment_score / count

            # Check for existing summary record
            existing_summary = (
                supabase.from_("stock_news_summary_30")
                .select("id")
                .eq("stockID", stock_id)
                .eq("date", date)
                .execute()
            )

            # Update or insert the average sentiment score
            if existing_summary.data:
                update_response = (
                    supabase.from_("stock_news_summary_30")
                    .update({"transformer_mean": average_sentiment})
                    .eq("stockID", stock_id)
                    .eq("date", date)
                    .execute()
                )
                if update_response.data:
                    print(
                        f"Updated transformer_mean for stockID {stock_id} on date {date} to {average_sentiment}"
                    )
                else:
                    print(
                        f"Failed to update transformer_mean for stockID {stock_id} on date {date}. Response: {update_response}"
                    )

            else:
                print(
                    f"No existing summary found for stockID {stock_id} on date {date}. No update performed."
                )


def plot_statistics():
    """
    生成圖表，顯示情緒和星級分佈
    """
    # 情緒分佈圖表
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    emotions = list(emotion_counts.keys())
    emotion_values = list(emotion_counts.values())
    plt.bar(emotions, emotion_values, color=["#84C1FF", "#FFE66F", "#FF5151"])
    plt.title("Emotion Distribution")
    plt.xlabel("Emotion Type")
    plt.ylabel("Count")

    # 星級分佈圖表
    plt.subplot(1, 2, 2)
    stars = list(star_counts.keys())
    star_values = list(star_counts.values())
    plt.bar(stars, star_values, color="#84C1FF")
    plt.title("Star Rating Distribution")
    plt.xlabel("Star Rating")
    plt.ylabel("Count")

    plt.tight_layout()
    plt.show()


def main():
    """
    主程式入口，負責觸發情緒分析和存儲過程，並在完成後生成圖表
    """
    date = "2024-7-20"  # 指定分析的目標日期
    test_stocks = [{"stock_id": "2330", "stock_name": "台積電"}]

    print("Starting sentiment analysis...")
    asyncio.run(analyze_and_store_sentiments(date, test_stocks))
    print("Sentiment analysis completed.")

    # 在分析完成後生成統計圖表
    plot_statistics()


if __name__ == "__main__":
    main()
