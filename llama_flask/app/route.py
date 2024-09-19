# 建立網頁的後端函數。
import sys
import os
import asyncio
from flask import render_template, request, jsonify
import llama_main_TogetherFlask as llama_main_TogetherFlask


def index():
    return render_template("index.html")  # 渲染出 html 檔，使用 render_template 函數


def root():
    return render_template("index.html")


def predict():
    stock_id = request.form["stock_id"]
    # 輸出 stock_id 以確認值
    print(f"Received stock_id: {stock_id}")
    dates = ["2019-12-31"]  # 假設你需要處理的日期，這可以根據需求動態獲取
    stock_ids = [stock_id]  # 將 stock_id 放入列表中

    result = llama_main_TogetherFlask.get_stock_predictions(
        dates, stock_ids
    )  # 預測邏輯函數
    return jsonify(result)
