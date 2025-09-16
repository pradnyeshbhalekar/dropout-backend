from mongoengine import Document, ReferenceField, ListField, StringField, DateTimeField
from models.student import StudentProfile
from models.user import User
import datetime

class Mentor(Document):
    user = ReferenceField(User, required=True, unique=True)  # linked user account
    assigned_students = ListField(ReferenceField(StudentProfile))  # students under mentor
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)

class MentorNote(Document):
    mentor = ReferenceField(Mentor, required=True)
    student = ReferenceField(StudentProfile, required=True)
    note = StringField(required=True)
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)