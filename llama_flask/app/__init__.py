# 建立 url 及 route 關聯
from flask import Flask
from app.route import index, predict


def create_app():
    app = Flask(__name__)
    # 載入配置，例如靜態檔案、模板等
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # 載入路由
    from .route import app as route_blueprint
    app.register_blueprint(route_blueprint)
    return app
