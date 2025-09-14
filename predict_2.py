import pandas as pd
import joblib

# Load the pre-trained model and scaler
model = joblib.load("logistic_model.joblib")
scaler = joblib.load("scaler.joblib")

# Load the dataset (or new data to predict)
data = pd.read_csv("dataset_2nd.csv")

# Preprocessing: scale features (assuming all columns except target)
X = data.drop(columns=['Target'], errors='ignore')  # remove target if present
X_scaled = scaler.transform(X)

# Predict probability of dropout
probabilities = model.predict_proba(X_scaled)[:, 1]  # probability of positive class

# Map probabilities to risk categories
def risk_category(prob):
    if prob < 0.34:
        return "Low Risk"
    elif prob < 0.67:
        return "Medium Risk"
    else:
        return "High Risk"

risk_labels = [risk_category(p) for p in probabilities]

# Add probability and risk category to the dataframe
data['Dropout_Probability'] = probabilities
data['Risk'] = risk_labels

# Save results to CSV
data.to_csv("predicted_risk.csv", index=False)
print("✅ Predictions with risk categories saved to 'predicted_risk.csv'")
print(data.head())
