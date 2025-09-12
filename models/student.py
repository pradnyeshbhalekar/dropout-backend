from mongoengine import Document,ReferenceField,IntField,StringField,DictField,BooleanField
import datetime

class StudentProfile(Document):
    # user = ReferenceField("User",required=True,unique=True)  #uncomment this when done with user for linking purpose
    age = IntField()
    gender = StringField(choice=['Male','Female','Other'])
    socioEconomicBackground = DictField()
    firstGenStudent = BooleanField()
    background = StringField(choices=["rural","urban"])

    course = StringField(required=True)
    year = IntField()
    semester = IntField()
    institutionType = StringField(choices=['public','private'])
    created_at = datetime.utcnow()
    