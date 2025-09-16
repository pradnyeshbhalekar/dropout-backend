from flask import Blueprint, request, jsonify
from extensions import bcrypt
import datetime, os, random
import jwt as pyjwt

dashboard_bp = Blueprint("dashboard", __name__)

# Load from env or defaults
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def decode_jwt(token):
    """Decode and verify JWT"""
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        return None  # expired
    except pyjwt.InvalidTokenError:
        return None  # invalid

def get_user_from_token():
    """Extract user from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded:
        return None, jsonify({"message": "Token is invalid or expired"}), 401

    return decoded, None, None

# Mock data generator functions
def generate_risk_distribution():
    """Generate mock risk distribution data"""
    return {
        "riskDistribution": [
            {
                "name": "Low Risk",
                "value": round(random.uniform(55, 70), 1),
                "color": "#10B981",
                "legendFontColor": "#374151",
                "legendFontSize": 12
            },
            {
                "name": "Medium Risk", 
                "value": round(random.uniform(15, 25), 1),
                "color": "#F59E0B",
                "legendFontColor": "#374151",
                "legendFontSize": 12
            },
            {
                "name": "High Risk",
                "value": round(random.uniform(15, 25), 1), 
                "color": "#EF4444",
                "legendFontColor": "#374151",
                "legendFontSize": 12
            }
        ]
    }

def generate_monthly_trends():
    """Generate mock monthly trends data"""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trends = []
    
    for month in months:
        trends.append({
            "month": month,
            "gpa": round(random.uniform(2.8, 4.0), 2),
            "attendance": random.randint(75, 95),
            "riskScore": random.randint(15, 35)
        })
    
    return {"monthlyTrends": trends}

def generate_dashboard_metrics():
    """Generate mock dashboard metrics"""
    return {
        "avgGpa": round(random.uniform(3.0, 3.8), 2),
        "avgAttendance": random.randint(80, 95),
        "gpaChange": round(random.uniform(-3.0, 5.0), 1),
        "attendanceChange": round(random.uniform(-5.0, 3.0), 1),
        "totalStudents": random.randint(150, 300),
        "atRiskStudents": random.randint(20, 60)
    }

@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard_data():
    """Get comprehensive dashboard data"""
    user_data, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code

    try:
        # Generate mock data (in production, this would fetch from database)
        metrics = generate_dashboard_metrics()
        risk_data = generate_risk_distribution()
        trends_data = generate_monthly_trends()

        dashboard_data = {
            **metrics,
            **risk_data,
            **trends_data,
            "lastUpdated": datetime.datetime.utcnow().isoformat(),
            "userId": user_data.get("userId"),
            "userRole": user_data.get("role")
        }

        return jsonify({
            "success": True,
            "data": dashboard_data,
            "message": "Dashboard data retrieved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch dashboard data: {str(e)}"
        }), 500

@dashboard_bp.route("/dashboard/metrics", methods=["GET"])
def get_dashboard_metrics():
    """Get basic dashboard metrics"""
    user_data, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code

    try:
        metrics = generate_dashboard_metrics()
        return jsonify({
            "success": True,
            "data": metrics,
            "message": "Metrics retrieved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch metrics: {str(e)}"
        }), 500

@dashboard_bp.route("/dashboard/risk-distribution", methods=["GET"])
def get_risk_distribution():
    """Get risk distribution data"""
    user_data, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code

    try:
        risk_data = generate_risk_distribution()
        return jsonify({
            "success": True,
            "data": risk_data,
            "message": "Risk distribution data retrieved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch risk distribution: {str(e)}"
        }), 500

@dashboard_bp.route("/dashboard/trends", methods=["GET"])
def get_monthly_trends():
    """Get monthly trends data"""
    user_data, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code

    try:
        trends_data = generate_monthly_trends()
        return jsonify({
            "success": True,
            "data": trends_data,
            "message": "Monthly trends data retrieved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch trends data: {str(e)}"
        }), 500

@dashboard_bp.route("/dashboard/student-summary", methods=["GET"])
def get_student_summary():
    """Get individual student summary"""
    user_data, error_response, status_code = get_user_from_token()
    if error_response:
        return error_response, status_code

    try:
        # Generate mock student-specific data
        student_data = {
            "currentGpa": round(random.uniform(2.5, 4.0), 2),
            "attendanceRate": random.randint(70, 100),
            "riskLevel": random.choice(["Low Risk", "Medium Risk", "High Risk"]),
            "coursesEnrolled": random.randint(4, 8),
            "creditsCompleted": random.randint(30, 120),
            "semester": "Fall 2024",
            "predictedOutcome": "Continue",
            "recommendedActions": [
                "Maintain current academic performance",
                "Consider joining study groups",
                "Meet with academic advisor monthly"
            ]
        }

        return jsonify({
            "success": True,
            "data": student_data,
            "message": "Student summary retrieved successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to fetch student summary: {str(e)}"
        }), 500