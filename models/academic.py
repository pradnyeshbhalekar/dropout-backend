from mongoengine import Document,ReferenceField,IntField,StringField,DictField,BooleanField,FloatField
from models.student import StudentProfile

class AcademicRecord(Document):
    student = ReferenceField(StudentProfile,required=True)
    semester = IntField(required=True)
    gpa = FloatField()
    backlogs = IntField(default=0)