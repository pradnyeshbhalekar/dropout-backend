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

# Make predictions
predictions = model.predict(X_scaled)

# Add predictions to the dataframe
data['Predictions'] = predictions

# Save predictions to CSV
data.to_csv("predictions.csv", index=False)
print("Predictions saved to predictions.csv")
