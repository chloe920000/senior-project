"""
pip install --upgrade numpy tensorflow transformers
pip install plotly
pip install kaleido

"""

import asyncio
from transformers import BertTokenizer, BertForSequenceClassification, pipeline
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd
import base64
from io import BytesIO

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


async def analyze_and_store_sentiments(date, stock):
    """
    分析並存儲距離指定日期前 30 天範圍內、指定股票的新聞情緒。
    date: string 日期 (格式: "YYYY-MM-DD")
    stock: dict 包含 stock_id 的字典
    """
    stock_id = stock.get("stock_id")
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)

    print("date:", date)

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
        print(f"Data already exists for stockID {stock_id} on date {date}. Skipping...")
        return  # Skip this stock_id since it has already been processed

    # Continue with sentiment analysis and data processing
    response = (
        supabase.from_("news_test")  # news_content
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
        return

    total_sentiment_score = 0
    count = 0
    new_with_sentiment = []

    for news in news_data:
        try:
            print(f"Processing news ID: {news['id']} for stock_id: {stock_id}")

            # Perform sentiment analysis
            sentiment_result = bert_sentiment_analysis(news["content"])
            sentiment_score = sentiment_result["score"]
            # star = sentiment_result["star"]
            # emotion = sentiment_result["emotion"]

            # Accumulate sentiment score
            total_sentiment_score += sentiment_score
            count += 1
            news["sentiment"] = sentiment_score
            new_with_sentiment.append(news)
            """
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
                        #"star": star,
                        #"emotion": emotion,
                    }
                )
                .execute()
            )

            if insert_response.data:
                print(f"Successfully inserted sentiment for news ID: {news['id']}")
            else:
                print(
                    f"Failed to insert sentiment for news ID {news['id']}. Response: {insert_response}"
                )"""

        except Exception as e:
            print(f"Failed to process news ID {news['id']}. Error: {str(e)}")

    # Calculate and store the average sentiment score if count > 0
    if count > 0:
        average_sentiment = total_sentiment_score / count

        if existing_summary.data:
            update_response = (
                supabase.from_("stock_news_summary_30")
                .update(
                    {"transformer_mean": average_sentiment, "count": count}
                )  # 合併兩個字段為一個字典
                .eq("stockID", stock_id)
                .eq("date", date)
                .execute()
            )

            if update_response.data:
                print(
                    f"Updated transformer_mean and count for stockID {stock_id} on date {date}."
                )
            else:
                print(f"Failed to update transformer_mean. Response: {update_response}")
    else:
        print(f"No valid sentiment data found for stockID {stock_id} on date {date}.")

    return average_sentiment, new_with_sentiment


def plot_sentiment_timeseries(news_with_sentiment):
    # 1. 資料處理
    data = pd.DataFrame(news_with_sentiment)
    data["date"] = pd.to_datetime(data["date"])
    daily_sentiment = data.groupby("date")["sentiment"].mean().reset_index()
    # 2. 繪製圖表
    fig = px.line(
        daily_sentiment,
        x="date",
        y="sentiment",
        title="Daily Average Sentiment Score Over Time",
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Average Sentiment Score")

    # 3. 將圖表儲存至內存並轉為 Base64 字符串
    img_bytes = BytesIO()
    fig.write_image(img_bytes, format="png")  # 儲存為 PNG 格式
    img_bytes.seek(0)

    # 編碼為 Base64
    img_base64 = base64.b64encode(img_bytes.read()).decode("utf-8")

    # 4. 返回 Base64 編碼字符串
    return img_base64


async def main():
    # 主程式入口，負責觸發情緒分析和存儲過程，並在完成後生成圖表
    date = "2024-07-20"  # 指定分析的目標日期
    stock = {"stock_id": "2330", "stock_name": "台積電"}  # 改為單一股票字典

    print("Starting sentiment analysis...")

    # 呼叫 analyze_and_store_sentiments，並檢查回傳的值
    result = await analyze_and_store_sentiments(date, stock)

    # 檢查 result 是否為 None，如果不是則進行解包
    if result is not None:
        average_sentiment, news_with_sentiment = result

        if news_with_sentiment:
            print("視覺化產生中...")

            plot_sentiment_timeseries(news_with_sentiment)
            print("30 days mean:", average_sentiment)

    print("Sentiment analysis completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e).startswith("This event loop is already running"):
            print("An event loop is already running. Skipping asyncio.run.")
            asyncio.get_running_loop().create_task(main())
        else:
            raise
