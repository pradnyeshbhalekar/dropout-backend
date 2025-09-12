from flask import Flask
from pymongo import MongoClient
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

