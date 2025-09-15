import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


df = pd.read_csv("dataset_2nd.csv", sep=",")
df = df[df['Target'] != 'Enrolled']
df.head()
print(df.info())
print(df.isnull().sum())
le = LabelEncoder()
print(df.head())
print(df.columns)
# Example: encode 'Target' column
df['Target'] = le.fit_transform(df['Target'])

# Encode other categorical columns (like Gender, etc.)
for col in df.select_dtypes(include=['object']).columns:
    df[col] = le.fit_transform(df[col])
X = df.drop('Target', axis=1)   # All features except Target
y = df['Target']                # Target column
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix")
plt.show()

joblib.dump(model, "logistic_model.joblib")
print("✅ Model saved successfully as 'logistic_model.joblib' in the current folder.")

# Save the fitted scaler in the current working directory
joblib.dump(scaler, "scaler.joblib")
print("✅ Scaler saved successfully as 'scaler.joblib' in the current folder.")

