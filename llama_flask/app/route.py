# 建立網頁的後端函數。
from flask import render_template


def hello_world():
    return "Hello, MVC框架!"


def index():
    return render_template("index.html")  # 渲染出 html 檔，使用 render_template 函數
