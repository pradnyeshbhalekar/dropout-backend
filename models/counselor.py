from mongoengine import Document, ReferenceField, ListField, StringField, DateTimeField
from models.student import StudentProfile
from models.user import User
import datetime

class Counselor(Document):
    user = ReferenceField(User, required=True, unique=True)  # linked user account
    userId = StringField()  # for easier access to user ID
    assigned_students = ListField(ReferenceField(StudentProfile))  # students under counselor
    department = StringField()  # counselor's department
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)
    
    def get_all_students(self):
        """Get all students assigned to this counselor from StudentProfile collection"""
        from models.student import StudentProfile
        return StudentProfile.objects(counselor=self)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "userId": self.userId or str(self.user.userId) if self.user else None,
            "name": self.user.name if self.user else None,
            "department": self.department,
            "totalStudents": len(self.assigned_students),
            "createdAt": self.createdAt.isoformat(),
            "updatedAt": self.updatedAt.isoformat()
        }

class CounselorNote(Document):
    counselor = ReferenceField(Counselor, required=True)
    student = ReferenceField(StudentProfile, required=True)
    note = StringField(required=True)
    createdAt = DateTimeField(default=datetime.datetime.utcnow)
    updatedAt = DateTimeField(default=datetime.datetime.utcnow)
