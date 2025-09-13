from mongoengine import (
    Document,
    ReferenceField,
    IntField,
    StringField,
    DictField,
    BooleanField,
    DateTimeField
)
import datetime
from models.user import User

class StudentProfile(Document):
    user = ReferenceField("User", required=True, unique=True)  

    age = IntField()
    gender = StringField(choices=['Male', 'Female', 'Other'])
    socioEconomicBackground = DictField()
    firstGenStudent = BooleanField()
    background = StringField(choices=["rural", "urban"])

    course = StringField(required=True)
    year = IntField()
    semester = IntField()
    institutionType = StringField(choices=['public', 'private'])

    created_at = DateTimeField(default=datetime.datetime.utcnow)
