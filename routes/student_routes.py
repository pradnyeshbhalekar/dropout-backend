from flask import Blueprint, request, jsonify
from models.student import StudentProfile
from models.user import User
import csv, io
<<<<<<< HEAD
from bson import json_util

student_bp = Blueprint("student", __name__)

# ==========================
# 1. Student Management (Core CRUD)
# ==========================

# Create a student profile (manual entry, not CSV)
@student_bp.route("/student", methods=["POST"])
def create_student():
    data = request.json
    user = User.objects(userId=data.get("userId")).first()
    if not user:
        return jsonify({"error": "User not found, create User first"}), 404

    profile = StudentProfile(
        user=user,
        age=data.get("age"),
        gender=data.get("gender"),
        socioEconomicBackground={
            "incomeLevel": data.get("incomeLevel"),
            "parentOccupation": data.get("parentOccupation"),
        },
        firstGenStudent=data.get("firstGenStudent", False),
        background=data.get("background"),
        course=data.get("course"),
        year=data.get("year", 1),
        semester=data.get("semester", 1),
        institutionType=data.get("institutionType", "public"),
    ).save()

    return jsonify({
        "message": "Student profile created successfully",
        "profileId": str(profile.id)
    }), 201

#working
# Fetch student profile
@student_bp.route("/student/<userId>", methods=["GET"])
def get_student(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    profile_data = {
        "id": str(profile.id),
        "userId": user.userId,
        "name": user.name,
        "age": profile.age,
        "gender": profile.gender,
        "socioEconomicBackground": profile.socioEconomicBackground,
        "firstGenStudent": profile.firstGenStudent,
        "background": profile.background,
        "course": profile.course,
        "year": profile.year,
        "semester": profile.semester,
        "institutionType": profile.institutionType,
        "created_at": profile.created_at.isoformat() if profile.created_at else None
    }

    return jsonify(profile_data), 200

#working
# Update student info
@student_bp.route("/student/update/<userId>", methods=["PUT"])
def update_student(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    data = request.json
    profile.update(**data)

    return jsonify({"message": "Student profile updated successfully"}), 200





# List all students (pagination + search)
from flask import jsonify, request

@student_bp.route("/students", methods=["GET"], endpoint="list_students")
def list_students():
    search = request.args.get("search", "").strip()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    # Filter only student users
    student_users = User.objects(role="student")

    # Apply search filter (by name or userId)
    if search:
        student_users = student_users.filter(name__icontains=search) | student_users.filter(userId__icontains=search)

    student_ids = [u.id for u in student_users]

    # Fetch student profiles
    profiles = StudentProfile.objects(user__in=student_ids).skip(skip).limit(limit)
    total = StudentProfile.objects(user__in=student_ids).count()

    students = []
    for p in profiles:
        # Include only StudentProfile fields and minimal user info
        student_data = {
            "id": str(p.id),
            "userId": p.user.userId if p.user else None,
            "name": p.user.name if p.user else None,
            "age": p.age,
            "gender": p.gender,
            "socioEconomicBackground": p.socioEconomicBackground,
            "firstGenStudent": p.firstGenStudent,
            "background": p.background,
            "course": p.course,
            "year": p.year,
            "semester": p.semester,
            "institutionType": p.institutionType,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        students.append(student_data)

    return jsonify({
        "students": students,
        "page": page,
        "limit": limit,
        "total": total
    }), 200



# ==========================
# 2. Bulk Upload via CSV
# ==========================
@student_bp.route("/student/profile/csv", methods=["POST"])
def upload_student_csv():
    file = request.files.get("file")
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    reader = csv.DictReader(io.StringIO(file.stream.read().decode("UTF-8")))
    created_profiles = []

    for row in reader:
        user = User.objects(userId=row["userId"]).first()
=======

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
>>>>>>> main
        if not user:
            skipped.append({"row": idx, "reason": "User not found", "userId": row.get('userId')})
            continue
<<<<<<< HEAD
        profile = StudentProfile(
            user=user,
            age=int(row.get("age", 0)),
            gender=row.get("gender"),
            socioEconomicBackground={
                "incomeLevel": row.get("incomeLevel"),
                "parentOccupation": row.get("parentOccupation"),
            },
            firstGenStudent=row.get("firstGenStudent", "False").lower() == "true",
            background=row.get("background"),
            course=row.get("course"),
            year=int(row.get("year", 1)),
            semester=int(row.get("semester", 1)),
            institutionType=row.get("institutionType", "public"),
        ).save()
        created_profiles.append(str(profile.id))

    return jsonify({
        "message": "Students uploaded",
        "profiles": created_profiles
    }), 201
 
=======

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
>>>>>>> main
