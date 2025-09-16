import pandas as pd
import joblib
import os
import sys

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, Blueprint, request
from models.user import User
from models.counselor import Counselor

# 🔹 Missing imports for counselor + jwt
from routes.auth import decode_jwt

# ========== CONFIG ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_dir = os.path.join(BASE_DIR, "../test_files")  # path to your CSVs

# CSV paths
academic_path = os.path.join(csv_dir, "academic.csv")
attendance_path = os.path.join(csv_dir, "attendance.csv")
curricular_path = os.path.join(csv_dir, "curricular.csv")
financial_path = os.path.join(csv_dir, "financial.csv")
students_path = os.path.join(csv_dir, "students.csv")

# Model paths
model_path = os.path.join(BASE_DIR, "logistic_model.joblib")
scaler_path = os.path.join(BASE_DIR, "scaler.joblib")

# ========== LOAD CSVs ==========
academic = pd.read_csv(academic_path)
attendance = pd.read_csv(attendance_path)
curricular = pd.read_csv(curricular_path)
financial = pd.read_csv(financial_path)
students = pd.read_csv(students_path)

# ========== MERGE BASE DATA ==========
df = students.merge(financial, on='userId', how='left')

# ========== DERIVE FEATURES ==========
df['Debtor'] = df['tuitionStatus'].eq('delayed').astype(int)
df['Tuition fees up to date'] = df['tuitionStatus'].eq('on-time').astype(int)
df['Scholarship holder'] = df['scholarship'].astype(int)

# Convert Gender to numeric (consistent with training)
df['Gender'] = df['Gender'].map({'Male': 1, 'Female': 0})

df['Age at enrollment'] = df['Age at enrollment']
df['Daytime/evening attendance'] = 1  # default
df['Educational special needs'] = 0   # default

# ========== MAP CURRICULAR UNITS (SAFE) ==========
for sem in [1, 2]:
    temp = curricular[curricular['semester'] == sem][
        ['userId', 'enrolled_units', 'approved_units', 'average_grade']
    ]
    if sem == 1:
        temp = temp.rename(columns={
            'enrolled_units': 'Curricular units 1st sem (enrolled)',
            'approved_units': 'Curricular units 1st sem (approved)',
            'average_grade': 'Curricular units 1st sem (grade)'
        })
    else:
        temp = temp.rename(columns={
            'enrolled_units': 'Curricular units 2nd sem (enrolled)',
            'approved_units': 'Curricular units 2nd sem (approved)',
            'average_grade': 'Curricular units 2nd sem (grade)'
        })
    df = df.merge(temp, on='userId', how='left')

# Fill missing curricular columns with 0
for col in [
    'Curricular units 1st sem (enrolled)',
    'Curricular units 1st sem (approved)',
    'Curricular units 1st sem (grade)',
    'Curricular units 2nd sem (enrolled)',
    'Curricular units 2nd sem (approved)',
    'Curricular units 2nd sem (grade)'
]:
    if col not in df.columns:
        df[col] = 0
    else:
        df[col] = df[col].fillna(0)

# Drop duplicate columns if any
df = df.loc[:, ~df.columns.duplicated()]

# ========== FINAL FEATURE LIST ==========
feature_cols = [
    'Daytime/evening attendance',
    'Educational special needs',
    'Debtor',
    'Tuition fees up to date',
    'Gender',
    'Scholarship holder',
    'Age at enrollment',
    'Curricular units 1st sem (enrolled)',
    'Curricular units 1st sem (approved)',
    'Curricular units 1st sem (grade)',
    'Curricular units 2nd sem (enrolled)',
    'Curricular units 2nd sem (approved)',
    'Curricular units 2nd sem (grade)'
]

X = df[feature_cols]

# ========== LOAD MODEL & SCALER ==========
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

print("🔍 Scaler expects:", list(scaler.feature_names_in_))
print("🔍 You provided:", list(X.columns))

# Ensure same feature order as training
X = X[scaler.feature_names_in_]

# ========== SCALE & PREDICT ==========
X_scaled = scaler.transform(X)
probabilities = model.predict_proba(X_scaled)[:, 1]

def risk_category(prob):
    if prob < 0.34:
        return "Low Risk"
    elif prob < 0.67:
        return "Medium Risk"
    else:
        return "High Risk"

df['Dropout_Probability'] = probabilities
df['Risk'] = [risk_category(p) for p in probabilities]

df.to_csv("predicted_risk.csv", index=False)
print("✅ Predictions saved to 'predicted_risk.csv'")
print(df[['userId', 'Dropout_Probability', 'Risk']])

# ========== HELPERS (used in counselor/student routes) ==========
def build_features():
    return df, X  # since you already built them globally

def make_predictions(df, X):
    results = []
    for _, row in df.iterrows():
        results.append({
            "userId": row["userId"],
            "Dropout_Probability": row["Dropout_Probability"],
            "Risk": row["Risk"]
        })
    return results

# ========== FLASK APP ==========
predict_bp = Blueprint("predict", __name__)

@predict_bp.route("/predict", methods=["GET"])
def home():
    return jsonify({"message": "Dropout Risk Prediction API is running 🚀"})

@predict_bp.route("/predict_batch", methods=["GET"])
def predict_batch():
    return jsonify(df[['userId', 'Dropout_Probability', 'Risk']].to_dict(orient="records"))

# ---------- Counselor predictions ----------
@predict_bp.route("/predict/counselor", methods=["GET"])
def predict_for_counselor():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded.get("role") != "counselor":
        return jsonify({"message": "Unauthorized"}), 403

    # 🔑 Lookup User by userId from token
    user = User.objects(userId=decoded["userId"]).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    # 🔑 Lookup Counselor by linked User
    counselor = Counselor.objects(user=user).first()
    if not counselor:
        return jsonify({"message": "Counselor profile not found"}), 404

    # Get assigned student userIds
    assigned_ids = [s.userId for s in counselor.assigned_students if s.userId]

    df, X = build_features()
    results = make_predictions(df, X)
    filtered = [r for r in results if r["userId"] in assigned_ids]

    return jsonify(filtered)

# ---------- Per-student prediction with clean fields ----------
@predict_bp.route("/predict/student/<studentId>", methods=["GET"])
def predict_for_student(studentId):
    # Rebuild features & predictions
    df_full, X = build_features()
    results = make_predictions(df_full, X)

    # Filter CSV data for this student
    student_csv_data = df_full[df_full['userId'] == studentId]

    if student_csv_data.empty:
        return jsonify({"message": "Student not found"}), 404

    # Get only predictions for this student
    student_prediction = next((r for r in results if r["userId"] == studentId), None)

    # Combine CSV data with predictions
    student_data_with_prediction = student_csv_data.to_dict(orient="records")[0]
    student_data_with_prediction.update({
        "Dropout_Probability": student_prediction["Dropout_Probability"],
        "Risk": student_prediction["Risk"]
    })

    # Remove any duplicate _x or _y columns
    cleaned_data = {k: v for k, v in student_data_with_prediction.items() if not k.endswith("_x") and not k.endswith("_y")}

    return jsonify(cleaned_data)
