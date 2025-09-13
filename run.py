# run.py
from flask import Flask
from extensions import bcrypt
from dotenv import load_dotenv
import os
from mongoengine import connect

load_dotenv()  # loads .env

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # connect to MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/Users")
    # mongoengine.connect accepts a single string host for full URI
    connect(host=mongo_uri)

    # init extensions
    bcrypt.init_app(app)

    # import and register blueprints (import here so mongoengine models are available)
    from routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
