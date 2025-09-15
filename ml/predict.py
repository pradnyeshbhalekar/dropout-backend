import pandas as pd
import joblib
import os

# ========== CONFIG ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_dir = os.path.join(BASE_DIR, "../test_files")  # path to new student CSVs

# CSV paths
students_path = os.path.join(csv_dir, "students.csv")
financial_path = os.path.join(csv_dir, "financial.csv")
curricular_path = os.path.join(csv_dir, "curricular.csv")

# Model paths
model_path = os.path.join(BASE_DIR, "logistic_model.joblib")
scaler_path = os.path.join(BASE_DIR, "scaler.joblib")

# ========== LOAD CSVs ==========
students = pd.read_csv(students_path)
financial = pd.read_csv(financial_path)
curricular = pd.read_csv(curricular_path)

# ========== MERGE STUDENTS WITH FINANCIAL ==========
df = students.merge(financial, on='userId', how='left')

# ========== DERIVE FEATURES ==========
df['Debtor'] = df['tuitionStatus'].eq('delayed').astype(int)
df['Tuition fees up to date'] = df['tuitionStatus'].eq('on-time').astype(int)
df['Scholarship holder'] = df['scholarship'].astype(int)

# Gender mapping
df['Gender'] = df['Gender'].map({'Male':1, 'Female':0})

# Age & defaults
df['Age at enrollment'] = df['Age at enrollment']
df['Daytime/evening attendance'] = df['Daytime/evening attendance']
df['Educational special needs'] = df['Educational special needs']

# ========== REMOVE PRECOMPUTED CURRICULAR COLUMNS IF PRESENT ==========
for col in [
    "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)",
    "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)"
]:
    if col in df.columns:
        df = df.drop(columns=[col])

# ========== MAP CURRICULAR UNITS ==========
for sem in [1, 2]:
    temp = curricular[curricular['semester']==sem][['userId','enrolled_units','approved_units','average_grade']]
    suffix = f'_sem{sem}'
    temp = temp.rename(columns={
        'enrolled_units': f'enrolled_units{suffix}',
        'approved_units': f'approved_units{suffix}',
        'average_grade': f'average_grade{suffix}'
    })
    df = df.merge(temp, on='userId', how='left')

# Fill missing curricular values with 0
for col in ['enrolled_units_sem1','approved_units_sem1','average_grade_sem1',
            'enrolled_units_sem2','approved_units_sem2','average_grade_sem2']:
    if col not in df.columns:
        df[col] = 0
    df[col] = df[col].fillna(0)

# Rename to match training features
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
    "Daytime/evening attendance",
    "Educational special needs",
    "Debtor",
    "Tuition fees up to date",
    "Gender",
    "Scholarship holder",
    "Age at enrollment",
    "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)",
    "Curricular units 2nd sem (enrolled)",
    "Curricular units 2nd sem (approved)",
    "Curricular units 2nd sem (grade)"
]

# Ensure all features exist and correct order
for col in feature_cols:
    if col not in df.columns:
        df[col] = 0

X = df[feature_cols]

# ========== LOAD MODEL & SCALER ==========
model = joblib.load(model_path)
scaler = joblib.load(scaler_path)

# ========== SCALE & PREDICT ==========
X_scaled = scaler.transform(X)
probabilities = model.predict_proba(X_scaled)[:, 1]

# ========== RISK CATEGORY FUNCTION ==========
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
output_path = os.path.join(BASE_DIR, "predicted_risk.csv")
df.to_csv(output_path, index=False)
print(f"✅ Predictions saved to '{output_path}'")
print(df[['userId','Dropout_Probability','Risk']])
