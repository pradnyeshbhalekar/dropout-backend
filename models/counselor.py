from mongoengine import Document, ReferenceField, ListField, StringField, DateTimeField, IntField
from models.student import StudentProfile
from models.user import User
import datetime


class Counselor(Document):
    user = ReferenceField(User, required=True, unique=True)   # linked user account
    specialization = StringField(required=True)               # counselor expertise
    experienceYears = IntField(default=0)                     # years of experience
    phone = StringField()                                     # contact number
    bio = StringField()                                       # optional bio

    assigned_students = ListField(ReferenceField(StudentProfile))  # students under counselor
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)


class CounselorNote(Document):
    counselor = ReferenceField(Counselor, required=True)
    student = ReferenceField(StudentProfile, required=True)
    note = StringField(required=True)
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)