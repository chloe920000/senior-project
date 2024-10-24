# 建立網頁的後端函數。
import re
from flask import (
    render_template,
    request,
    jsonify,
    Blueprint,
    Response,
    stream_with_context,
)
import app.services.llama_main_TogetherFlask as llama_main_TogetherFlask
import app.services.crawler_for_flask as crawler_for_flask  # 引入crawler_for_flask模塊
import app.services.score_mean as score_mean  # 引入score_mean模塊
import app.services.gemini_signal_to_supa as gemini_signal_to_supa  # 引入gemini_signal模塊
import app.services.sentiment_analysis_to_supa as sentiment_analysis_to_supa  # 引入sentiment_analysis模塊
import app.services.gemini_news_prompt as gemini_news_prompt
import app.services.crawler_for_flask as crawler_for_flask
from dotenv import load_dotenv
from supabase import create_client, Client
import os
from datetime import datetime
import time

# 加載環境變量
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# 建立 Blueprint
app = Blueprint("app", __name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")  # 渲染出 html 檔，使用 render_template 函數


@app.route("/predict", methods=["POST"])
def predict():
    # 從請求中獲取 stock_data
    stock_data = request.form["stock_data"]
    stock_id = None
    stock_name = None

    # 檢查 stock_data 是否是四位數字
    if re.match(r"^\d{4}$", stock_data):
        stock_id = stock_data
    # 檢查 stock_data 是否是中文
    elif re.match(r"[\u4e00-\u9fff]+", stock_data):
        stock_name = stock_data
    else:
        return jsonify({"error": "Invalid stock data format"}), 400  # 返回錯誤訊息

    # 確保至少 stock_id 或 stock_name 其中一個有值
    if not stock_id and not stock_name:
        return (
            jsonify(
                {"error": "At least one of stock_id or stock_name must be provided."}
            ),
            400,
        )

    # 如果只有 stock_name 沒有 stock_id，從 Supabase 查詢 stockID
    if not stock_id and stock_name:
        stock_response = (
            supabase.from_("stock")
            .select("stockID")
            .eq("stock_name", stock_name)
            .execute()
        )
        stock_data = stock_response.data

        if not stock_data or len(stock_data) == 0:
            return (
                jsonify({"error": f"No stockID found for stock_name: {stock_name}"}),
                404,
            )

        # 獲取 stockID
        stock_id = stock_data[0]["stockID"]

    # 如果只有 stock_id 沒有 stock_name，從 Supabase 查詢 stock_name
    if not stock_name and stock_id:
        stock_response = (
            supabase.from_("stock")
            .select("stock_name")
            .eq("stockID", stock_id)
            .execute()
        )
        stock_data = stock_response.data

        if not stock_data or len(stock_data) == 0:
            return (
                jsonify({"error": f"No stock_name found for stockID: {stock_id}"}),
                404,
            )

        # 獲取 stock_name
        stock_name = stock_data[0]["stock_name"]

    # 構建 stocks 列表
    stocks = [{"stock_id": stock_id, "stock_name": stock_name}]
    # 輸出 stocks 列表
    print("Stocks list:", stocks)

    # 確保 stocks 列表不為空
    if not stocks:
        return jsonify({"error": "Stocks list cannot be empty."}), 400

    # (op.1)指定 date 為當日
    # date = datetime.today().strftime("%Y-%m-%d")
    # (op.2)自由指定 date
    date = datetime.today().strftime("%Y-%m-%d")
    print("Today Date:", date)

    # 日期放入 dates 列表
    dates = [date]  # 假設你需要處理的日期，這可以根據需求動態獲取

    # 獲取股票預測結果
    result = llama_main_TogetherFlask.get_stock_predictions(dates, stocks)

    # 刪除無關新聞，標記好、不好，並寫入supa
    gemini_score = gemini_signal_to_supa.get_gemini_response(date, stocks)

    # 將剩餘新聞情緒評分
    sentiment_score = sentiment_analysis_to_supa.get_sentiment_score(date, stocks)

    # 30天新聞摘要

    #30天的新聞summary分析 
    gemini_30dnews_response = gemini_news_prompt.get_gemini_30dnews_response(date , stocks)
    # 計算新聞情緒平均分數，將 stocks 列表作為參數傳遞
    sentiment_mean = score_mean.scoreMean(date, stocks)

    # return jsonify(combined_result)
    return jsonify(result, gemini_30dnews_response, sentiment_mean)


# 用來做前端的 SSE 股票分析跑馬燈
@app.route("/sse_stock_analysis")
def sse_stock_analysis():
    def generate_stock_data():
        # 模擬股票分析數據的逐步生成
        analysis_steps = [
            "Fetching stock data...",
            "Analyzing trends...",
            "Calculating metrics...",
            "Generating predictions...",
        ]
        for step in analysis_steps:
            yield f"data: {step}\n\n"  # SSE 格式
            time.sleep(1)  # 模擬延遲

        yield "data: 分析完成!\n\n"  # 最終消息

    return Response(
        stream_with_context(generate_stock_data()), content_type="text/event-stream"
    )


@app.route("/news", methods=["POST"])
def news():
    # Fetch stock ID from form data
    stock_id = request.form.get("stock_data")

    if not stock_id:
        return jsonify({"error": "Stock ID is required"}), 400

    # Get stock name from Supabase
    stock_name = crawler_for_flask.get_stock_name(stock_id)

    if not stock_name:
        return jsonify({"error": f"Stock name for ID {stock_id} not found"}), 404

    # Fetch news from various sources
    news_ltn = crawler_for_flask.fetch_news_ltn(stock_id, stock_name)
    news_tvbs = crawler_for_flask.fetch_news_tvbs(stock_id, stock_name)
    news_cnye = crawler_for_flask.fetch_news_cnye(stock_id, stock_name)
    news_chinatime = crawler_for_flask.fetch_news_chinatime(stock_id, stock_name)

    # Return news data as JSON response
    return jsonify(
        {
            "ltn": news_ltn,
            "tvbs": news_tvbs,
            "cnye": news_cnye,
            "chinatime": news_chinatime,
        }
    )
