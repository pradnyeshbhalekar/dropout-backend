import pandas as pd
import joblib
import os

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
df['Gender'] = df['Gender'].map({'Male':1, 'Female':0})
df['Age at enrollment'] = df['Age at enrollment']
df['Daytime/evening attendance'] = 1  # default
df['Educational special needs'] = 0   # default

# ========== MAP CURRICULAR UNITS ==========
for sem in [1, 2]:
    temp = curricular[curricular['semester'] == sem][['userId','enrolled_units','approved_units','average_grade']]
    suffix = f'_sem{sem}'
    temp = temp.rename(columns={
        'enrolled_units': f'enrolled_units{suffix}',
        'approved_units': f'approved_units{suffix}',
        'average_grade': f'average_grade{suffix}'
    })
    df = df.merge(temp, on='userId', how='left')

# Rename to match model feature names
df.rename(columns={
    'enrolled_units_sem1': 'Curricular units 1st sem (enrolled)',
    'approved_units_sem1': 'Curricular units 1st sem (approved)',
    'average_grade_sem1': 'Curricular units 1st sem (grade)',
    'enrolled_units_sem2': 'Curricular units 2nd sem (enrolled)',
    'approved_units_sem2': 'Curricular units 2nd sem (approved)',
    'average_grade_sem2': 'Curricular units 2nd sem (grade)'
}, inplace=True)

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

# ========== SAVE RESULTS ==========
df.to_csv("predicted_risk.csv", index=False)
print("✅ Predictions saved to 'predicted_risk.csv'")
print(df[['userId','Dropout_Probability','Risk']])
