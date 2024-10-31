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


def bert_sentiment_analysis(news):
    """
    使用 nlptown 的多語言 BERT 模型進行情緒分析
    news: string 文章內容

    return: dict 包含 sentiment_score, star, 和 emotion (1: positive, 0: neutral, -1: negative)
    """
    result = sentiment_analyzer(news[:512])[0]  # 模型有 token 限制，這裡截取前512個字元
    sentiment_label = result["label"]  # 例如 "5 stars"
    sentiment_score = result["score"]  # 置信度分數

    # 提取星級數字，例如 "5 stars" -> 5
    star = int(sentiment_label.split()[0])

    # 根據星級設定情緒類型
    if star in [1, 2]:
        emotion = -1  # negative
        emotion_label = "negative"
    elif star == 3:
        emotion = 0  # neutral
        emotion_label = "neutral"
    else:
        emotion = 1  # positive
        emotion_label = "positive"

    # 統計情緒類型和星級
    emotion_counts[emotion_label] += 1
    star_counts[star] += 1

    return {
        "score": sentiment_score,  # 置信度分數 (浮點數)
        "star": star,  # 星級 (1 到 5)
        "emotion": emotion,  # 情緒類型 (1: positive, 0: neutral, -1: negative)
    }


async def analyze_and_store_sentiments(date, stocks):
    """
    分析並存儲距離指定日期前 30 天範圍內、指定股票的新聞情緒。
    date: string 日期 (格式: "YYYY-MM-DD")
    stocks: list 包含多個 stock_id 的列表
    """
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)

    for stock in stocks:
        stock_id = stock.get("stock_id")

        # Check if there's already an existing, non-empty `transformer_mean` for this stock_id and date
        existing_summary = (
            supabase.from_("stock_news_summary_30")
            .select("transformer_mean")
            .eq("stockID", stock_id)
            .eq("date", date)
            .execute()
        )

        if (
            existing_summary.data
            and existing_summary.data[0]["transformer_mean"] is not None
        ):
            print(
                f"Data already exists for stockID {stock_id} on date {date}. Skipping..."
            )
            continue  # Skip this stock_id since it has already been processed

        # Continue with sentiment analysis and data processing
        response = (
            supabase.from_("news_test")
            .select("*")
            .gte("date", start_date)
            .lte("date", end_date)
            .eq("stockID", stock_id)
            .execute()
        )
        news_data = response.data

        if not news_data:
            print(
                f"No news data found for stock_id {stock_id} within the specified date range."
            )
            continue

        total_sentiment_score = 0
        count = 0

        for news in news_data:
            try:
                print(f"Processing news ID: {news['id']} for stock_id: {stock_id}")

                # Perform sentiment analysis
                sentiment_result = bert_sentiment_analysis(news["content"])
                sentiment_score = sentiment_result["score"]
                star = sentiment_result["star"]
                emotion = sentiment_result["emotion"]

                # Accumulate sentiment score
                total_sentiment_score += sentiment_score
                count += 1

                # Insert sentiment data for each news item
                existing_sentiment = (
                    supabase.from_("transformer_sentiment")
                    .select("id")
                    .eq("news_id", news["id"])
                    .execute()
                )

                if existing_sentiment.data:
                    supabase.from_("transformer_sentiment").delete().eq(
                        "news_id", news["id"]
                    ).execute()

                insert_response = (
                    supabase.from_("transformer_sentiment")
                    .insert(
                        {
                            "news_id": news["id"],
                            "stockID": stock_id,
                            "sentiment": sentiment_score,
                            "star": star,
                            "emotion": emotion,
                        }
                    )
                    .execute()
                )

                if insert_response.data:
                    print(f"Successfully inserted sentiment for news ID: {news['id']}")
                else:
                    print(
                        f"Failed to insert sentiment for news ID {news['id']}. Response: {insert_response}"
                    )

            except Exception as e:
                print(f"Failed to process news ID {news['id']}. Error: {str(e)}")

        # Calculate and store the average sentiment score if count > 0
        if count > 0:
            average_sentiment = total_sentiment_score / count

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
                insert_response = (
                    supabase.from_("stock_news_summary_30")
                    .insert(
                        {
                            "stockID": stock_id,
                            "date": date,
                            "transformer_mean": average_sentiment,
                        }
                    )
                    .execute()
                )
                if insert_response.data:
                    print(
                        f"Inserted new transformer_mean for stockID {stock_id} on date {date} with average {average_sentiment}"
                    )
                else:
                    print(
                        f"Failed to insert transformer_mean for stockID {stock_id} on date {date}. Response: {insert_response}"
                    )


def main():
    """
    主程式入口，負責觸發情緒分析和存儲過程，並在完成後生成圖表
    """
    date = "2024-7-25"  # 指定分析的目標日期
    test_stocks = [{"stock_id": "2330", "stock_name": "台積電"}]

    print("Starting sentiment analysis...")
    asyncio.run(analyze_and_store_sentiments(date, test_stocks))
    print("Sentiment analysis completed.")


if __name__ == "__main__":
    main()
