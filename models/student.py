# models/student.py
from mongoengine import Document, StringField, DateTimeField
import datetime

class User(Document):
    meta = {"collection": "users"}  # optional but explicit
    userId = StringField(required=True, unique=True)   # STU001 / CNS001 / ADM001
    name = StringField(required=True)
    email = StringField()
    passwordHash = StringField(required=True)          # bcrypt hash
    role = StringField(required=True, choices=["student", "counselor", "admin"])
    status = StringField(default="active")             # active | inactive
    lastLogin = DateTimeField()
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "userId": self.userId,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "lastLogin": self.lastLogin.isoformat() if self.lastLogin else None,
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat(),
        }
