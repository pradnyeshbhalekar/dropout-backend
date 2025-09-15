"""
Alert and Notification Models for Student Risk Management
"""

from mongoengine import (
    Document, ReferenceField, StringField, DateTimeField,
    BooleanField, DictField, ListField, FloatField, IntField
)
from models.student import StudentProfile
from models.user import User
import datetime

class Alert(Document):
    """
    Model for storing student alerts based on risk factors
    """
    meta = {"collection": "alerts"}
    
    # References
    student = ReferenceField(StudentProfile, required=True)
    user = ReferenceField(User, required=True)  # The student user
    
    # Alert details
    alert_id = StringField(required=True, unique=True)
    alert_type = StringField(required=True, choices=[
        'attendance_drop',
        'gpa_drop',
        'assignment_missing',
        'failed_course',
        'risk_level_change',
        'financial_issue',
        'general_warning',
        'positive_feedback'
    ])
    
    severity = StringField(required=True, choices=['low', 'medium', 'high', 'critical'])
    title = StringField(required=True)
    message = StringField(required=True)
    
    # Trigger information
    trigger_data = DictField()  # Store the data that triggered the alert
    threshold_violated = StringField()  # e.g., "attendance < 75%"
    
    # Risk assessment
    risk_level = StringField(choices=['low', 'medium', 'high'])
    dropout_probability = FloatField()
    
    # Recommendations
    recommendations = ListField(StringField())
    resources = ListField(DictField())  # Links to helpful resources
    
    # Status tracking
    status = StringField(default='unread', choices=['unread', 'read', 'acknowledged', 'resolved'])
    read_at = DateTimeField()
    acknowledged_at = DateTimeField()
    resolved_at = DateTimeField()
    
    # Response tracking
    student_response = StringField()  # Optional student feedback
    action_taken = StringField()  # What action the student took
    
    # Timestamps
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    expires_at = DateTimeField()  # Optional expiry for time-sensitive alerts
    
    # Notification preferences
    sent_via_email = BooleanField(default=False)
    sent_via_sms = BooleanField(default=False)
    sent_via_push = BooleanField(default=False)
    
    def to_dict(self):
        """Convert alert to dictionary for API response"""
        return {
            "id": str(self.id),
            "alert_id": self.alert_id,
            "student_id": str(self.student.id) if self.student else None,
            "user_id": self.user.userId if self.user else None,
            "type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "risk_level": self.risk_level,
            "dropout_probability": self.dropout_probability,
            "recommendations": self.recommendations,
            "resources": self.resources,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class NotificationPreference(Document):
    """
    Model for storing user notification preferences
    """
    meta = {"collection": "notification_preferences"}
    
    user = ReferenceField(User, required=True, unique=True)
    
    # Channel preferences
    email_enabled = BooleanField(default=True)
    sms_enabled = BooleanField(default=False)
    push_enabled = BooleanField(default=True)
    
    # Alert type preferences (which types of alerts to receive)
    alert_types = DictField(default={
        'attendance_drop': True,
        'gpa_drop': True,
        'assignment_missing': True,
        'failed_course': True,
        'risk_level_change': True,
        'financial_issue': True,
        'general_warning': True,
        'positive_feedback': True
    })
    
    # Frequency preferences
    notification_frequency = StringField(
        default='immediate',
        choices=['immediate', 'daily', 'weekly', 'monthly']
    )
    
    # Quiet hours (no notifications during these times)
    quiet_hours_start = IntField(default=22)  # 10 PM
    quiet_hours_end = IntField(default=8)     # 8 AM
    
    # Severity threshold (only notify for this severity and above)
    min_severity = StringField(
        default='medium',
        choices=['low', 'medium', 'high', 'critical']
    )
    
    # Contact information
    email = StringField()
    phone = StringField()
    
    # Timestamps
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)


class RiskAssessment(Document):
    """
    Model for storing periodic risk assessments for students
    """
    meta = {"collection": "risk_assessments"}
    
    student = ReferenceField(StudentProfile, required=True)
    
    # Assessment details
    assessment_date = DateTimeField(default=datetime.datetime.utcnow)
    risk_level = StringField(required=True, choices=['low', 'medium', 'high'])
    previous_risk_level = StringField(choices=['low', 'medium', 'high'])
    dropout_probability = FloatField(required=True)
    confidence_score = FloatField()
    
    # Metrics at time of assessment
    metrics = DictField()  # Store all relevant metrics
    
    # Risk factors identified
    risk_factors = ListField(DictField())
    
    # Changes from previous assessment
    risk_increased = BooleanField(default=False)
    significant_changes = ListField(StringField())
    
    # Interventions suggested
    suggested_interventions = ListField(StringField())
    
    # Model information
    model_version = StringField()
    
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    
    def to_dict(self):
        """Convert assessment to dictionary"""
        return {
            "id": str(self.id),
            "student_id": str(self.student.id) if self.student else None,
            "assessment_date": self.assessment_date.isoformat(),
            "risk_level": self.risk_level,
            "previous_risk_level": self.previous_risk_level,
            "dropout_probability": self.dropout_probability,
            "confidence_score": self.confidence_score,
            "risk_factors": self.risk_factors,
            "risk_increased": self.risk_increased,
            "significant_changes": self.significant_changes,
            "suggested_interventions": self.suggested_interventions
        }


class AlertTemplate(Document):
    """
    Model for storing reusable alert templates
    """
    meta = {"collection": "alert_templates"}
    
    template_id = StringField(required=True, unique=True)
    alert_type = StringField(required=True)
    severity = StringField(required=True)
    
    # Template content with placeholders
    title_template = StringField(required=True)
    message_template = StringField(required=True)
    
    # Default recommendations for this type of alert
    default_recommendations = ListField(StringField())
    default_resources = ListField(DictField())
    
    # Activation rules
    activation_rules = DictField()  # Conditions that trigger this alert
    
    # Usage tracking
    times_used = IntField(default=0)
    last_used = DateTimeField()
    
    active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)