from flask import Blueprint, request, jsonify
from models.student import StudentProfile
from models.user import User
import csv, io

student_bp = Blueprint('student', __name__)

@student_bp.route('/student/profile/csv', methods=['POST'])
def upload_student_csv():
    """
    Upload a CSV with either full student info or financial/curricular info.
    Only updates fields present in the CSV to avoid ValidationError on required fields.
    """
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_profiles = []
    updated_profiles = []
    skipped = []

    for idx, row in enumerate(reader, start=1):
        user = User.objects(userId=row.get('userId')).first()
        if not user:
            skipped.append({"row": idx, "reason": "User not found", "userId": row.get('userId')})
            continue

        profile = StudentProfile.objects(user=user).first()
        try:
            if profile:
                # Update only fields present in CSV
                if 'age' in row or 'Age at enrollment' in row:
                    age_value = row.get('Age at enrollment', row.get('age'))
                    if age_value:
                        profile.age_at_enrollment = int(age_value)
                if 'gender' in row or 'Gender' in row:
                    gender_value = row.get('Gender', row.get('gender'))
                    if gender_value:
                        profile.gender = gender_value
                if 'incomeLevel' in row or 'parentOccupation' in row:
                    profile.socioEconomicBackground = {
                        "incomeLevel": row.get("incomeLevel", profile.socioEconomicBackground.get("incomeLevel")),
                        "parentOccupation": row.get("parentOccupation", profile.socioEconomicBackground.get("parentOccupation")),
                    }
                if 'firstGenStudent' in row:
                    profile.firstGenStudent = row.get('firstGenStudent', str(profile.firstGenStudent)).lower() == 'true'
                if 'background' in row:
                    profile.background = row.get('background', profile.background)
                if 'course' in row:
                    profile.course = row.get('course', profile.course)
                if 'year' in row:
                    profile.year = int(row.get('year', profile.year))
                if 'semester' in row:
                    profile.semester = int(row.get('semester', profile.semester))
                if 'institutionType' in row:
                    profile.institutionType = row.get('institutionType', profile.institutionType)
                if 'special_needs' in row:
                    profile.special_needs = row.get('special_needs', str(profile.special_needs)).lower() == 'true'
                if 'session_type' in row:
                    profile.session_type = row.get('session_type', profile.session_type)
                
                # Optional: add financial/curricular fields if present
                if 'Daytime/evening attendance' in row:
                    profile.attendance_type = row.get('Daytime/evening attendance', getattr(profile, 'attendance_type', None))
                if 'Educational special needs' in row:
                    profile.educational_special_needs = row.get('Educational special needs', getattr(profile, 'educational_special_needs', 0)) == '1'
                if 'Debtor' in row:
                    profile.debtor = row.get('Debtor', getattr(profile, 'debtor', 0)) == '1'
                if 'Tuition fees up to date' in row:
                    profile.tuition_up_to_date = row.get('Tuition fees up to date', getattr(profile, 'tuition_up_to_date', 0)) == '1'
                if 'Scholarship holder' in row:
                    profile.scholarship_holder = row.get('Scholarship holder', getattr(profile, 'scholarship_holder', 0)) == '1'
                if 'Curricular units 1st sem (enrolled)' in row:
                    profile.curricular_units = profile.curricular_units or {}
                    profile.curricular_units['1st_sem'] = {
                        "enrolled": int(row.get('Curricular units 1st sem (enrolled)', 0)),
                        "approved": int(row.get('Curricular units 1st sem (approved)', 0)),
                        "grade": float(row.get('Curricular units 1st sem (grade)', 0.0))
                    }
                if 'Curricular units 2nd sem (enrolled)' in row:
                    profile.curricular_units = profile.curricular_units or {}
                    profile.curricular_units['2nd_sem'] = {
                        "enrolled": int(row.get('Curricular units 2nd sem (enrolled)', 0)),
                        "approved": int(row.get('Curricular units 2nd sem (approved)', 0)),
                        "grade": float(row.get('Curricular units 2nd sem (grade)', 0.0))
                    }

                profile.save()
                updated_profiles.append(str(profile.id))
            else:
                # For CSV files without course/background, create profile with default values
                # Check if this CSV has the basic required data (age, gender)
                if 'Age at enrollment' not in row and 'age' not in row:
                    skipped.append({"row": idx, "reason": "Missing age data", "userId": row.get('userId')})
                    continue
                    
                if 'Gender' not in row and 'gender' not in row:
                    skipped.append({"row": idx, "reason": "Missing gender data", "userId": row.get('userId')})
                    continue

                # Use defaults for missing required fields
                age = int(row.get('Age at enrollment', row.get('age', 18)))
                gender = row.get('Gender', row.get('gender'))
                course = row.get('course', 'General Studies')  # Default course
                background = row.get('background', 'urban')    # Default background
                
                profile = StudentProfile(
                    user=user,
                    age_at_enrollment=age,
                    gender=gender,
                    socioEconomicBackground={
                        "incomeLevel": row.get("incomeLevel", "medium"),
                        "parentOccupation": row.get('parentOccupation', "unknown"),
                    },
                    firstGenStudent=row.get('firstGenStudent', 'False').lower() == 'true',
                    background=background,
                    course=course,
                    year=int(row.get('year', 1)),
                    semester=int(row.get('semester', 1)),
                    institutionType=row.get('institutionType', 'public'),
                    special_needs=row.get('special_needs', 'False').lower() == 'true',
                    session_type=row.get('session_type', 'day'),
                    # Add new fields from CSV
                    attendance_type=row.get('Daytime/evening attendance'),
                    educational_special_needs=row.get('Educational special needs', '0') == '1',
                    debtor=row.get('Debtor', '0') == '1',
                    tuition_up_to_date=row.get('Tuition fees up to date', '1') == '1',
                    scholarship_holder=row.get('Scholarship holder', '0') == '1'
                )
                
                # Add curricular units data if present
                if 'Curricular units 1st sem (enrolled)' in row:
                    profile.curricular_units = profile.curricular_units or {}
                    profile.curricular_units['1st_sem'] = {
                        "enrolled": int(row.get('Curricular units 1st sem (enrolled)', 0)),
                        "approved": int(row.get('Curricular units 1st sem (approved)', 0)),
                        "grade": float(row.get('Curricular units 1st sem (grade)', 0.0))
                    }
                if 'Curricular units 2nd sem (enrolled)' in row:
                    profile.curricular_units = profile.curricular_units or {}
                    profile.curricular_units['2nd_sem'] = {
                        "enrolled": int(row.get('Curricular units 2nd sem (enrolled)', 0)),
                        "approved": int(row.get('Curricular units 2nd sem (approved)', 0)),
                        "grade": float(row.get('Curricular units 2nd sem (grade)', 0.0))
                    }
                
                profile.save()
                created_profiles.append(str(profile.id))
        except Exception as e:
            skipped.append({"row": idx, "reason": str(e), "userId": row.get('userId')})

    return jsonify({
        'message': "Students uploaded/updated",
        'created_profiles': created_profiles,
        'updated_profiles': updated_profiles,
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