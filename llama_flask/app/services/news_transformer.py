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
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import jieba
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


# 中文分詞器與句子分割器
class ChineseTokenizer:
    def tokenize(self, text):
        return list(jieba.cut(text))  # 分詞

    def to_sentences(self, text):
        delimiters = ["。", "！", "？"]
        sentences = []
        start = 0
        for i, char in enumerate(text):
            if char in delimiters:
                sentences.append(text[start : i + 1].strip())
                start = i + 1
        if start < len(text):  # 如果還有剩餘的文本
            sentences.append(text[start:].strip())
        return sentences

    def to_words(self, text):
        return self.tokenize(text)  # 实现 to_words 方法，调用 tokenize 方法


# 使用 Sumy 生成 512 字新聞摘要
def summarize_text(news, tokenizer, word_limit=512):
    sentences = tokenizer.to_sentences(news)
    parser = PlaintextParser.from_string(" ".join(sentences), tokenizer)
    summarizer = LsaSummarizer()
    preliminary_summary = summarizer(parser.document, 10)
    summary_text = " ".join(str(sentence) for sentence in preliminary_summary)
    if len(summary_text) > word_limit:
        summary_text = summary_text[:word_limit] + "..."
    return summary_text


def bert_sentiment_analysis(news):
    """
    使用 nlptown 的多語言 BERT 模型進行情緒分析
    news: string 文章內容

    return: dict 包含 sentiment_score, star, 和 emotion (1: positive, 0: neutral, -1: negative)
    """
    tokenizer = ChineseTokenizer()
    summarized_news = summarize_text(news, tokenizer, word_limit=512)
    result = sentiment_analyzer(summarized_news)[0]
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
        return existing_summary.data[0]["transformer_mean"], []  # 確保有返回值

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
        print(f"No news data found for stock_id {stock_id} within the specified date range.")
        return None, []  # 確保有返回值

    total_sentiment_score = 0
    count = 0
    new_with_sentiment = []

    for news in news_data:
        try:
            print(f"Processing news ID: {news['id']} for stock_id: {stock_id}")

            # Perform sentiment analysis
            sentiment_result = bert_sentiment_analysis(news["content"])
            sentiment_score = sentiment_result["score"]

            # Accumulate sentiment score
            total_sentiment_score += sentiment_score
            count += 1
            news["sentiment"] = sentiment_score
            new_with_sentiment.append(news)

        except Exception as e:
            print(f"Failed to process news ID {news['id']}. Error: {str(e)}")

    # Calculate and store the average sentiment score if count > 0
    if count > 0:
        average_sentiment = round(total_sentiment_score / count, 4)

        if existing_summary.data:
            update_response = (
                supabase.from_("stock_news_summary_30")
                .update({"transformer_mean": average_sentiment, "count": count})
                .eq("stockID", stock_id)
                .eq("date", date)
                .execute()
            )

            if update_response.data:
                print(f"Updated transformer_mean and count for stockID {stock_id} on date {date}.")
            else:
                print(f"Failed to update transformer_mean. Response: {update_response}")
    else:
        print(f"No valid sentiment data found for stockID {stock_id} on date {date}.")
        average_sentiment = None  # 如果沒有有效的數據，設為 None

    return average_sentiment, new_with_sentiment



def plot_sentiment_timeseries(news_with_sentiment):
    try:
        # 1. Data processing
        data = pd.DataFrame(news_with_sentiment)
        if "date" not in data.columns or "sentiment" not in data.columns:
            raise ValueError(
                "The input data must contain 'date' and 'sentiment' columns."
            )

        data["date"] = pd.to_datetime(data["date"])
        daily_sentiment = data.groupby("date")["sentiment"].mean().reset_index()

        # 2. Plot the chart
        print("Generating chart...")
        fig = px.line(
            daily_sentiment,
            x="date",
            y="sentiment",
            title="Daily Average Sentiment Score Over Time",
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Average Sentiment Score")

        # 3. Save the chart as an HTML file
        # html_filename = "try_sentiment_chart.html"
        # fig.write_html(html_filename)
        # print(f"Chart saved as HTML: {html_filename}")

        # 4. Convert the chart to HTML string
        plot_html = fig.to_html(
            full_html=False
        )  # Convert to HTML snippet without full HTML structure
        print("Chart to_html() generated successfully.")

        # 4. Return the HTML string
        return plot_html

    except Exception as e:
        print(f"Error: {e}")
        return None


"""
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
"""
