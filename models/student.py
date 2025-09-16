# models/student.py
from mongoengine import (
    Document, ReferenceField, IntField, StringField,
    DictField, BooleanField, DateTimeField
)
import datetime

class StudentProfile(Document):
    user = ReferenceField("User", required=True, unique=True)
    counselor = ReferenceField("Counselor")  # assigned counselor
    userId = StringField()  # for easier access to user ID

    age_at_enrollment = IntField()
    gender = StringField(choices=['Male', 'Female', 'Other'])
    special_needs = BooleanField(default=False)  # new
    session_type = StringField(choices=['day', 'evening'])  # new
    socioEconomicBackground = DictField()
    firstGenStudent = BooleanField()
    background = StringField(choices=["rural", "urban"])

    course = StringField(required=True)
    year = IntField()
    semester = IntField()
    institutionType = StringField(choices=['public', 'private'])
    
    # Additional fields for CSV upload compatibility
    attendance_type = StringField()  # Daytime/evening attendance
    educational_special_needs = BooleanField(default=False)
    debtor = BooleanField(default=False)
    tuition_up_to_date = BooleanField(default=True)
    scholarship_holder = BooleanField(default=False)
    curricular_units = DictField()  # Store curricular unit data

    # predicted outcome label (optional)
    risk_label = StringField(choices=['low', 'medium', 'high'])

    created_at = DateTimeField(default=datetime.datetime.utcnow)
