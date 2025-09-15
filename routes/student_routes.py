from flask import Blueprint, request, jsonify
from models.student import StudentProfile
from models.user import User
import csv, io

student_bp = Blueprint('student', __name__)


@student_bp.route('/student/profile/csv', methods=['POST'])
def upload_student_csv():
    """
    Upload a CSV with columns:
    userId,age,gender,incomeLevel,parentOccupation,firstGenStudent,
    background,course,year,semester,institutionType,special_needs,session_type
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_profiles = []
    skipped = []

    for idx, row in enumerate(reader, start=1):
        user = User.objects(userId=row.get('userId')).first()
        if not user:
            skipped.append({"row": idx, "reason": "User not found", "userId": row.get('userId')})
            continue

        try:
            profile = StudentProfile(
                user=user,
                age_at_enrollment=int(row.get('age', 0)),
                gender=row.get('gender'),
                socioEconomicBackground={
                    "incomeLevel": row.get("incomeLevel"),
                    "parentOccupation": row.get('parentOccupation'),
                },
                firstGenStudent=row.get('firstGenStudent', 'False').lower() == 'true',
                background=row.get('background'),
                course=row.get('course'),
                year=int(row.get('year', 1)),
                semester=int(row.get('semester', 1)),
                institutionType=row.get('institutionType', 'public'),
                special_needs=row.get('special_needs', 'False').lower() == 'true',
                session_type=row.get('session_type')
            ).save()
            created_profiles.append(str(profile.id))
        except Exception as e:
            skipped.append({"row": idx, "reason": str(e), "userId": row.get('userId')})

    return jsonify({
        'message': "Students uploaded",
        'profiles': created_profiles,
        'skipped': skipped
    }), 201


@student_bp.route('/student/profile/<user_id>', methods=['PATCH'])
def update_student_profile(user_id):
    data = request.get_json() or {}
    user_obj = User.objects(userId=user_id).first()
    if not user_obj:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user_obj).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    # Only update fields present in data
    updatable_fields = [
        'age_at_enrollment', 'gender', 'socioEconomicBackground', 'firstGenStudent',
        'background', 'course', 'year', 'semester', 'institutionType', 'special_needs', 'session_type'
    ]
    for field in updatable_fields:
        if field in data:
            setattr(profile, field, data[field])

    profile.save()
    return jsonify({"message": "Profile updated", "id": str(profile.id)}), 200



@student_bp.route('/student/profile/<user_id>', methods=['GET'])
def get_student_profile(user_id):
    user_obj = User.objects(userId=user_id).first()
    if not user_obj:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user_obj).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    return jsonify({
        "id": str(profile.id),
        "userId": user_id,
        "gender": profile.gender,
        "age_at_enrollment": profile.age_at_enrollment,
        "background": profile.background,
        "course": profile.course,
        "year": profile.year,
        "semester": profile.semester,
        "institutionType": profile.institutionType,
        "special_needs": profile.special_needs,
        "session_type": profile.session_type,
        "socioEconomicBackground": profile.socioEconomicBackground,
        "firstGenStudent": profile.firstGenStudent
    }), 200