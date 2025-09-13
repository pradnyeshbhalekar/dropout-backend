from flask import Blueprint,request,jsonify
from models.student import StudentProfile
from models.user import User
import csv,io

student_bp = Blueprint('student',__name__)

@student_bp.route('/student/profile/csv',methods=['POST'])
def upload_student_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({"message":"No file uploaded"}),400
    
    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_profiles=[]

    for row in reader:
        user = User.objects(userId=row['userId']).first()
        if not user:
            continue
        profile = StudentProfile(
            user=user,
            age = int(row.get('age',0)),
            gender = row.get('gender'),
            socioEconomicBackground = {
                "incomeLevel": row.get("incomeLevel"),
                "parentOccupation": row.get('parentOccupation'),
            },
            firstGenStudent = row.get('firstGenStudent','False').lower() == 'true',
            background=row.get('background'),
            course = row.get('course'),
            year = int(row.get('year',1)),
            semester = int(row.get('semester',1)),
            institutionType = row.get('institutionType','public')
        ).save()
        created_profiles.append(str(profile.id))

    return jsonify({'message':"Students uploaded",
                        'profiles': created_profiles}),201