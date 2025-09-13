from flask_bcrypt import Bcrypt
from dotenv import load_dotenv   # ✅ to use load_dotenv
import os                        # ✅ to use os.getenv
from mongoengine import connect  # ✅ to use connect for MongoDB

bcrypt = Bcrypt()

# Load .env variables
load_dotenv()

def init_db():
    MONGO_URI = os.getenv("MONGO_URI")
    connect(host=MONGO_URI)   # connect from mongoengine
