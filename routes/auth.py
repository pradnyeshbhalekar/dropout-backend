# routes/auth.py
from flask import Blueprint, request, jsonify
from models.user import User
from extensions import bcrypt
from utils.utils import generate_user_id, email_in_use, userId_in_use
import datetime, os, jwt

auth_bp = Blueprint("auth", __name__)

# Load from env or defaults
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY = int(os.getenv("JWT_EXPIRY", 3600))  # seconds


def create_jwt(user):
    """Generate JWT for a user"""
    payload = {
        "userId": user.userId,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRY),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token):
    """Decode and verify JWT"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None  # expired
    except jwt.InvalidTokenError:
        return None  # invalid


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

    # Generate JWT
    token = create_jwt(user)

    return jsonify({
        "message": f"Welcome {user.name}",
        "user": {"userId": user.userId, "name": user.name, "role": user.role},
        "token": token
    }), 200


# ---------- Protected route example ----------
@auth_bp.route("/profile", methods=["GET"])
def profile():
    """Example protected route"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded:
        return jsonify({"message": "Token is invalid or expired"}), 401

    user = User.objects(userId=decoded["userId"]).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "userId": user.userId,
        "name": user.name,
        "role": user.role
    }), 200


# ---------- Logout ----------
@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    With JWT, logout is usually handled client-side (just delete the token).
    Optionally, maintain a token blacklist for server-side invalidation.
    """
    return jsonify({"message": "You have been logged out successfully"}), 200


# ---------- Forgot Password ----------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"message": "email is required"}), 400

    user = User.objects(email=email, status="active").first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Create a short-lived reset token (15 min)
    reset_token = jwt.encode(
        {
            "userId": user.userId,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
            "iat": datetime.datetime.utcnow()
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    # Normally you would email this to the user
    return jsonify({
        "message": "Password reset token generated. (Send via email in production)",
        "resetToken": reset_token
    }), 200


# ---------- Reset Password ----------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    reset_token = data.get("token")
    new_password = data.get("newPassword")

    if not reset_token or not new_password:
        return jsonify({"message": "token and newPassword are required"}), 400

    try:
        decoded = jwt.decode(reset_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Reset token expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid reset token"}), 400

    user = User.objects(userId=decoded["userId"], status="active").first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Hash new password
    pw_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
    user.passwordHash = pw_hash
    user.updatedAt = datetime.datetime.utcnow()
    user.save()

    return jsonify({"message": "Password has been reset successfully"}), 200
