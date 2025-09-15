from mongoengine import Document, ReferenceField, IntField, FloatField
from models.student import StudentProfile

class CurricularUnit(Document):
    student = ReferenceField(StudentProfile, required=True)
    semester = IntField(required=True)
    enrolled_units = IntField(required=True)
    approved_units = IntField(required=True)
    average_grade = FloatField(required=True)
