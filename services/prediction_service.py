"""
Prediction Service for Student Dropout Risk Assessment
This module integrates the pre-trained ML model with the Flask backend
"""

import pandas as pd
import joblib
import numpy as np
from typing import Dict, List, Optional
import os
from datetime import datetime

class PredictionService:
    def __init__(self, model_path: str = "models/ml/logistic_model.joblib", 
                 scaler_path: str = "models/ml/scaler.joblib"):
        """
        Initialize the prediction service with pre-trained model and scaler
        
        Args:
            model_path: Path to the saved model file
            scaler_path: Path to the saved scaler file
        """
        self.model = None
        self.scaler = None
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.load_model()
    
    def load_model(self):
        """Load the pre-trained model and scaler"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                print(f"✅ Model loaded successfully from {self.model_path}")
            else:
                print(f"⚠️ Model files not found. Please ensure model files exist at {self.model_path} and {self.scaler_path}")
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
    
    def prepare_student_features(self, student_data: Dict) -> pd.DataFrame:
        """
        Prepare student data for prediction
        
        Args:
            student_data: Dictionary containing student metrics
            
        Returns:
            DataFrame with prepared features
        """
        # Define feature mapping based on your dataset
        features = {
            'age_at_enrollment': student_data.get('age_at_enrollment', 18),
            'gender_encoded': 1 if student_data.get('gender') == 'Male' else 0,
            'marital_status': student_data.get('marital_status', 0),
            'application_mode': student_data.get('application_mode', 1),
            'application_order': student_data.get('application_order', 1),
            'course': student_data.get('course_id', 1),
            'daytime_evening_attendance': 1 if student_data.get('session_type') == 'day' else 0,
            'previous_qualification': student_data.get('previous_qualification', 1),
            'previous_qualification_grade': student_data.get('previous_qualification_grade', 100),
            'admission_grade': student_data.get('admission_grade', 100),
            'displaced': 1 if student_data.get('displaced', False) else 0,
            'debtor': 1 if student_data.get('debtor', False) else 0,
            'tuition_fees_up_to_date': 1 if student_data.get('tuition_status') == 'on-time' else 0,
            'scholarship_holder': 1 if student_data.get('scholarship', False) else 0,
            'curricular_units_1st_sem_enrolled': student_data.get('sem1_enrolled_units', 6),
            'curricular_units_1st_sem_approved': student_data.get('sem1_approved_units', 5),
            'curricular_units_1st_sem_grade': student_data.get('sem1_grade', 12),
            'curricular_units_2nd_sem_enrolled': student_data.get('sem2_enrolled_units', 6),
            'curricular_units_2nd_sem_approved': student_data.get('sem2_approved_units', 5),
            'curricular_units_2nd_sem_grade': student_data.get('sem2_grade', 12),
            'unemployment_rate': student_data.get('unemployment_rate', 10.0),
            'inflation_rate': student_data.get('inflation_rate', 2.0),
            'gdp': student_data.get('gdp', 1.0)
        }
        
        # Add attendance percentage if available
        if 'attendance_percentage' in student_data:
            features['attendance_rate'] = student_data['attendance_percentage']
        
        # Add GPA if available
        if 'current_gpa' in student_data:
            features['current_gpa'] = student_data['current_gpa']
            
        return pd.DataFrame([features])
    
    def predict_risk(self, student_data: Dict) -> Dict:
        """
        Predict dropout risk for a single student
        
        Args:
            student_data: Dictionary containing student information
            
        Returns:
            Dictionary with risk prediction results
        """
        if not self.model or not self.scaler:
            return {
                'error': 'Model not loaded',
                'risk_level': 'unknown',
                'probability': 0.0
            }
        
        try:
            # Prepare features
            features_df = self.prepare_student_features(student_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features_df)
            
            # Predict probability
            probability = self.model.predict_proba(features_scaled)[0, 1]
            
            # Determine risk level
            risk_level = self.categorize_risk(probability)
            
            # Get feature importance for explanation
            feature_importance = self.get_risk_factors(student_data, probability)
            
            return {
                'student_id': student_data.get('userId'),
                'risk_level': risk_level,
                'dropout_probability': float(probability),
                'risk_factors': feature_importance,
                'prediction_date': datetime.utcnow().isoformat(),
                'confidence': self.calculate_confidence(probability)
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {str(e)}")
            return {
                'error': str(e),
                'risk_level': 'unknown',
                'probability': 0.0
            }
    
    def categorize_risk(self, probability: float) -> str:
        """
        Categorize risk based on dropout probability
        
        Args:
            probability: Dropout probability (0-1)
            
        Returns:
            Risk category string
        """
        if probability < 0.33:
            return "low"
        elif probability < 0.67:
            return "medium"
        else:
            return "high"
    
    def calculate_confidence(self, probability: float) -> float:
        """
        Calculate prediction confidence
        Higher confidence when probability is closer to 0 or 1
        """
        distance_from_middle = abs(probability - 0.5) * 2
        return min(0.95, 0.6 + distance_from_middle * 0.35)
    
    def get_risk_factors(self, student_data: Dict, probability: float) -> List[Dict]:
        """
        Identify key risk factors contributing to the prediction
        
        Returns:
            List of risk factors with their impact levels
        """
        risk_factors = []
        
        # Check attendance
        attendance = student_data.get('attendance_percentage', 100)
        if attendance < 75:
            risk_factors.append({
                'factor': 'Low Attendance',
                'value': f"{attendance}%",
                'impact': 'high' if attendance < 60 else 'medium',
                'recommendation': 'Improve class attendance to at least 75%'
            })
        
        # Check GPA
        gpa = student_data.get('current_gpa', 4.0)
        if gpa < 2.5:
            risk_factors.append({
                'factor': 'Low GPA',
                'value': f"{gpa:.2f}",
                'impact': 'high' if gpa < 2.0 else 'medium',
                'recommendation': 'Seek academic support to improve grades'
            })
        
        # Check failed units
        failed_units = student_data.get('failed_units', 0)
        if failed_units > 0:
            risk_factors.append({
                'factor': 'Failed Courses',
                'value': str(failed_units),
                'impact': 'high' if failed_units > 2 else 'medium',
                'recommendation': 'Consider retaking failed courses or seeking tutoring'
            })
        
        # Check financial status
        if student_data.get('tuition_status') == 'delayed':
            risk_factors.append({
                'factor': 'Tuition Payment Delays',
                'value': 'Delayed',
                'impact': 'medium',
                'recommendation': 'Contact financial aid office for payment plans'
            })
        
        # Check scholarship status
        if not student_data.get('scholarship', False) and probability > 0.5:
            risk_factors.append({
                'factor': 'No Scholarship',
                'value': 'Not enrolled',
                'impact': 'low',
                'recommendation': 'Explore scholarship opportunities'
            })
        
        return risk_factors
    
    def batch_predict(self, students_data: List[Dict]) -> List[Dict]:
        """
        Predict risk for multiple students
        
        Args:
            students_data: List of student data dictionaries
            
        Returns:
            List of prediction results
        """
        predictions = []
        for student_data in students_data:
            prediction = self.predict_risk(student_data)
            predictions.append(prediction)
        return predictions
    
    def update_model(self, new_model_path: str, new_scaler_path: str):
        """
        Update the model with a new version
        
        Args:
            new_model_path: Path to the new model
            new_scaler_path: Path to the new scaler
        """
        self.model_path = new_model_path
        self.scaler_path = new_scaler_path
        self.load_model()

# Singleton instance
prediction_service = PredictionService()