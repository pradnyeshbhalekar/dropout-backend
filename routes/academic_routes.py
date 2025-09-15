from flask import Blueprint,request,jsonify
from models.student import StudentProfile
from models.academic import AcademicRecord
import csv,io
from models.user import User

academic_profile = Blueprint('academic',__name__)


@academic_profile.route('/academic',methods=['POST'])
def upload_academic_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({
            "message":"No file uploaded"
        }),400
    
    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_records = []
    
    for row in reader:
        user_obj = User.objects(userId=row["userId"]).first()
        if not user_obj:
            continue

        profile = StudentProfile.objects(user=user_obj).first()
        if not profile:
            continue

        record = AcademicRecord(
            student = profile,
            semester = int(row['semester']),
            gpa = float(row.get('gpa',0)),
            backlogs = int(row.get('backlogs',0))
        ).save()

        created_records.append(str(record.id))

    return jsonify({
        "mesage":"Academic records uploaded successfully",
        'records':created_records
    }),201
