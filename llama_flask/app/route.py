# 建立網頁的後端函數。
import re
from flask import render_template, request, jsonify
from flask import Blueprint, render_template, request, jsonify
import app.services.llama_main_TogetherFlask as llama_main_TogetherFlask
import app.services.score_mean as score_mean  # 引入score_mean模塊
from dotenv import load_dotenv
from supabase import create_client, Client
import os

# 加載環境變量
load_dotenv()

# Supabase 配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# 建立 Blueprint
app = Blueprint('app', __name__)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")  # 渲染出 html 檔，使用 render_template 函數

@app.route('/predict', methods=['POST'])
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

    # 指定 dates 列表
    dates = ["2024-07-30"]  # 假設你需要處理的日期，這可以根據需求動態獲取

    # 獲取股票預測結果
    result = llama_main_TogetherFlask.get_stock_predictions(dates, stocks)

    # 計算新聞情緒平均分數，將 stocks 列表作為參數傳遞
    sentiment_mean = score_mean.scoreMean(dates, stocks)


    # return jsonify(combined_result)
    return jsonify(sentiment_mean,result)
