# backend/app.py
import os
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from mongoengine import connect  
from extensions import bcrypt

# Azure/GitHub Models imports
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

from config import Config

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY

# Enable CORS for React Native frontend
CORS(app, origins="*")

# Database connection
connect(
    db=Config.DB_NAME,
    host=Config.MONGO_URI,
    alias='default'
)

# Init bcrypt
bcrypt.init_app(app)

# ----------------- ROUTES IMPORTS -----------------
from routes.auth import auth_bp  
from routes.academic_routes import academic_profile
from routes.student_routes import student_bp
from routes.attendance_routes import attendance_bp
from routes.financial_routes import financial_bp
from routes.curricular_routes import curricular_bp
from routes.dashboard_routes import dashboard_bp
from routes.counselor_routes import counselor_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(student_bp, url_prefix="/api")
app.register_blueprint(academic_profile, url_prefix='/api')
app.register_blueprint(attendance_bp, url_prefix='/api')
app.register_blueprint(financial_bp, url_prefix='/api')
app.register_blueprint(curricular_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp, url_prefix='/api')
app.register_blueprint(counselor_bp, url_prefix='/api')


# ----------------- CHATBOT ENDPOINT -----------------
# Get GitHub token securely
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("❌ GITHUB_TOKEN is missing. Please set it as an environment variable.")

# Initialize GitHub Models client
client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(GITHUB_TOKEN),
)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()

        if not user_input:
            return jsonify({"error": "Message cannot be empty"}), 400

        # Call GitHub Models directly
        response = client.complete(
            messages=[
                SystemMessage("You are a kind, empathetic, and supportive counselling chatbot. "
                              "Provide short, calming, and helpful advice in a friendly tone."),
                UserMessage(user_input),
            ],
            model="openai/gpt-4o-mini"
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------- MAIN ENTRY -----------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)