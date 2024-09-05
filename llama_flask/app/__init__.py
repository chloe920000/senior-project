# 建立 url 及 route 關聯
from flask import Flask
from app.route import index, predict


def create_app():
    app = Flask(__name__)
    app.add_url_rule("/", "/", index)
    app.add_url_rule("/predict", "predict", predict, methods=["POST"])
    return app
