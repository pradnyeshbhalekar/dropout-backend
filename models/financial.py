from mongoengine import Document,IntField,StringField,BooleanField,ReferenceField
from models.student import StudentProfile
class FinancialRecord(Document):
    student = ReferenceField(StudentProfile, required=True)
    tuitionStatus = StringField(choices=["on-time", "delayed"])
    scholarship = BooleanField(default=False)
    loanDependency = BooleanField(default=False)
