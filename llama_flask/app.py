from flask import Flask, request, jsonify, render_template
import llama_try  # 假設您的邏輯文件名為 llama_try.py

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # 簡單的輸入頁面

@app.route('/predict', methods=['POST'])
def predict():
    stock_id = request.form['stock_id']
    result = llama_try.get_stock_predictions(stock_id)  # 假設這是您的邏輯函數
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
