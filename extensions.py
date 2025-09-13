from flask_bcrypt import Bcrypt
from mongoengine import connect
import os
from dotenv import load_dotenv

bcrypt = Bcrypt()

# Load .env variables
load_dotenv()

def init_db():
    MONGO_URI = os.getenv("MONGO_URI")
    connect(host=MONGO_URI)
