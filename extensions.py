from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
<<<<<<< HEAD

# Load .env variables
load_dotenv()

def init_db():
    MONGO_URI = os.getenv("MONGO_URI")
    connect(host=MONGO_URI)
=======
>>>>>>> features/upload-student-details
