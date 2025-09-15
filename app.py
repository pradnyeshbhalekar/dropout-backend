from flask import Flask
from flask_bcrypt import Bcrypt
from config import Config
from mongoengine import connect  
from .extension import bcrypt


app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY


connect(
    db=Config.DB_NAME,
    host=Config.MONGO_URI,
    alias='default'
)

bcrypt.init_app(app)

from routes.auth import auth_bp  
from routes.academic_routes import academic_profile
from routes.student_routes import student_bp
from routes.attendance_routes import attendance_bp
from routes.financial_routes import financial_bp
from routes.curricular_routes import curricular_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(student_bp, url_prefix="/api")
app.register_blueprint(academic_profile, url_prefix='/api')
app.register_blueprint(attendance_bp, url_prefix='/api')
app.register_blueprint(financial_bp, url_prefix='/api')
app.register_blueprint(curricular_bp, url_prefix='/api')


if __name__ == "__main__":
    app.run(debug=True, port=5000)
