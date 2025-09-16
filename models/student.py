from mongoengine import (
    Document, ReferenceField, IntField, StringField,
    DictField, BooleanField, DateTimeField
)
import datetime

class StudentProfile(Document):
    user = ReferenceField("User", required=True, unique=True)

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

    # predicted outcome label (optional)
    risk_label = StringField(choices=['low', 'medium', 'high'])

    # ✅ new field: assigned counselor
    assigned_counselor = ReferenceField("Counselor", required=False)

    created_at = DateTimeField(default=datetime.datetime.utcnow)
