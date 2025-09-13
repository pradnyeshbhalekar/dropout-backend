# routes/auth.py
from flask import Blueprint, request, jsonify
from models.student import User
from extensions import bcrypt
from utils.utils import generate_user_id, email_in_use, userId_in_use
import datetime

auth_bp = Blueprint("auth", __name__)

# ---------- Signup ----------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    name = data.get("name")
    password = data.get("password")
    role = data.get("role", "student")
    email = data.get("email")
    userId = data.get("userId")  # optional if admin provides

    if not name or not password:
        return jsonify({"message": "name and password are required"}), 400

    if userId:
        if userId_in_use(userId):
            return jsonify({"message": "userId already exists"}), 400
    else:
        userId = generate_user_id(role)

    if email:
        if email_in_use(email):
            return jsonify({"message": "email already in use"}), 400

    # hash password
    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    now = datetime.datetime.utcnow()
    user = User(
        userId=userId,
        name=name,
        email=email,
        passwordHash=pw_hash,
        role=role,
        status="active",
        createdAt=now,
        updatedAt=now,
    )
    user.save()
    print("User saved", user.to_json())

    return jsonify({"message": "user created", "userId": userId}), 201


# ---------- Signin ----------
@auth_bp.route("/signin", methods=["POST"])
def signin():
    data = request.get_json() or {}
    userId = data.get("userId")
    email = data.get("email")
    password = data.get("password")

    if not password or (not userId and not email):
        return jsonify({"message": "provide (userId or email) and password"}), 400

    # find active user
    query = {}
    if userId:
        query["userId"] = userId
    else:
        query["email"] = email

    user = User.objects(**query, status="active").first()
    if not user:
        return jsonify({"message": "invalid credentials"}), 401

    if not bcrypt.check_password_hash(user.passwordHash, password):
        return jsonify({"message": "invalid credentials"}), 401

    # update lastLogin and updatedAt
    user.lastLogin = datetime.datetime.utcnow()
    user.updatedAt = datetime.datetime.utcnow()
    user.save()

    return jsonify({
        "message": f"Welcome {user.name}",
        "user": {"userId": user.userId, "name": user.name, "role": user.role}
    }), 200


# ---------- Logout ----------
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Dummy logout route — in future you can clear JWT or session here.
    For now it just returns success.
    """
    return jsonify({"message": "You have been logged out successfully"}), 200
