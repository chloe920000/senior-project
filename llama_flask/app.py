from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
from dotenv import load_dotenv
import llama_try  # 假設您的邏輯文件名為 llama_try.py
import os
import logging

app = Flask(__name__)

# 設置日誌級別
#logging.basicConfig(level=logging.DEBUG)

# 加載環境變量
load_dotenv()

# 設置Supabase連接
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/')
def index():
    return render_template('index.html')  # 簡單的輸入頁面

@app.route('/predict', methods=['POST'])
def predict():
    stock_id = request.form['stock_id']
    result = llama_try.get_stock_predictions(stock_id)  # 預測邏輯函數
    return jsonify(result)





#資料庫測試
@app.route('/test_supabase')
def test_supabase():
    try:
        response = supabase.table('test_table').select('*').execute()
        data = response.data
        app.logger.debug(f"Supabase query result: {data}")
        if not data:
            app.logger.debug("No data found in test_table")
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error querying Supabase: {e}")
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run('0.0.0.0')