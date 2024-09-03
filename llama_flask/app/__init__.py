# 建立 url 及 route 關聯
from flask import Flask
from app.route import hello_world, index


def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", "/", hello_world)
    app.add_url_rule("/index", "index", index)  # index 可以改成任何想顯示在 url 的文字
    return app
