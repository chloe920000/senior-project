from flask import Blueprint, render_template, request, jsonify
import app.services.llama_main_TogetherFlask as llama_main_TogetherFlask

# 建立 Blueprint
app = Blueprint('app', __name__)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")  # 渲染出 html 檔，使用 render_template 函數

@app.route('/predict', methods=['POST'])
def predict():
    stock_id = request.form.get("stock_id")
    
    # 輸出 stock_id 以確認值
    print(f"Received stock_id: {stock_id}")

    # 假設您要處理的日期，這裡我們用一個範例日期
    dates = ["2019-12-31"]
    stock_ids = [stock_id]  # 將 stock_id 放入列表中

    # 調用預測邏輯函數，並取得結果
    result = llama_main_TogetherFlask.get_stock_predictions(dates, stock_ids)

    # 返回 JSON 格式的結果
    return jsonify(result)
