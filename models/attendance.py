from mongoengine import Document,ReferenceField,IntField,FloatField,StringField
from models.student import StudentProfile

class Attendance(Document):
    student = ReferenceField(StudentProfile, required=True)
    semester = IntField(required=True)
    session_type = StringField(choices=['day', 'evening'])  # new if you want per-semester
    attendancePercentage = FloatField()
    absenteeDays = IntField()
