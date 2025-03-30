from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()  # 先创建实例

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 必须在注册蓝图前初始化
    login_manager.init_app(app)  # 绑定到app
    login_manager.login_view = 'main.login'  # 设置登录路由
    
    from app.routes import bp
    app.register_blueprint(bp)
    
    return app