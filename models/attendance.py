from mongoengine import Document,ReferenceField,IntField,FloatField
from models.student import StudentProfile

class Attendance(Document):
    student = ReferenceField(StudentProfile,required=True)
    semester = IntField(required=True)
    attendancePercentage = FloatField()
    absenteeDays = IntField()
