from flask import Flask
from flask_bootstrap import Bootstrap
<<<<<<< HEAD
from .config import Config

def create_app():
    app = Flask(__name__)
    Bootstrap(app)

    app.config.from_object(Config)
=======
from flask_sqlalchemy import SQLAlchemy
from .config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    bootstrap = Bootstrap(app)
    app.config.from_object(Config)
    db.init_app(app)

    from .forms import LoginForm
    from .routes import register_routes
    register_routes(app)


>>>>>>> origin/alex
    return app
    