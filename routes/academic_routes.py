from flask import Blueprint,request,jsonify
from models.student import StudentProfile
from models.academic import AcademicRecord
import csv,io
from models.user import User

academic_profile = Blueprint('academic',__name__)

#working
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
# ✅ Get academic records for a specific student
@academic_profile.route('/academic/<userId>', methods=['GET'])
def get_academic_records(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    records = AcademicRecord.objects(student=profile).order_by("semester")
    data = [
        {
            "semester": r.semester,
            "gpa": r.gpa,
            "backlogs": r.backlogs
        } for r in records
    ]

    return jsonify({
        "userId": userId,
        "records": data
    }), 200


# ✅ Get academic summary (CGPA, GPA per sem, backlog count)
@academic_profile.route('/academic/<userId>/summary', methods=['GET'])
def get_academic_summary(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    records = AcademicRecord.objects(student=profile)
    if not records:
        return jsonify({"message": "No academic records found"}), 404

    total_gpa = sum([r.gpa for r in records])
    cgpa = round(total_gpa / len(records), 2)
    total_backlogs = sum([r.backlogs for r in records])

    gpa_per_semester = {r.semester: r.gpa for r in records}

    return jsonify({
        "userId": userId,
        "cgpa": cgpa,
        "gpa_per_semester": gpa_per_semester,
        "total_backlogs": total_backlogs
    }), 200


# ✅ Filter academic records (by semester, GPA, etc.)
@academic_profile.route('/academic', methods=['GET'])
def filter_academic_records():
    semester = request.args.get("semester", type=int)
    min_gpa = request.args.get("min_gpa", type=float)

    query = {}
    if semester:
        query["semester"] = semester
    if min_gpa:
        query["gpa__gte"] = min_gpa

    records = AcademicRecord.objects(**query)
    data = [
        {
            "userId": r.student.user.userId,
            "semester": r.semester,
            "gpa": r.gpa,
            "backlogs": r.backlogs
        } for r in records
    ]

    return jsonify({"results": data}), 200