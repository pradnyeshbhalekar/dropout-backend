from mongoengine import connect
from config import Config

connect(
    db=Config.DB_NAME,
    host=Config.MONGO_URI
)