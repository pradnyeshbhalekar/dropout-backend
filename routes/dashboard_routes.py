# routes/dashboard.py
from flask import Blueprint, jsonify
from models.student import StudentProfile
from models.academic import AcademicRecord
from models.attendance import Attendance
from utils.dashboard_utils import calculate_risk_status
from models.user import User
from bson import ObjectId

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/student/<user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    # Try fetching user by _id first
    user = None
    try:
        user = User.objects(id=ObjectId(user_id)).first()
    except Exception:
        # If ObjectId conversion fails, ignore
        pass

    # If not found by _id, try userId field
    if not user:
        user = User.objects(userId=user_id).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    # Fetch StudentProfile
    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"message": "Student not found"}), 404

    # Fetch academic and attendance records
    academic_records = AcademicRecord.objects(student=profile).order_by('semester')
    attendance_records = Attendance.objects(student=profile).order_by('semester')

    # Map attendance by semester
    attendance_map = {att.semester: att for att in attendance_records}

    dashboard = []
    for record in academic_records:
        att = attendance_map.get(record.semester, None)
        attendancePercentage = att.attendancePercentage if att else None
        absenteeDays = att.absenteeDays if att else None

        dashboard.append({
            "semester": record.semester,
            "gpa": record.gpa,
            "cgpa": getattr(record, "cgpa", None),
            "backlogs": record.backlogs,
            "attendancePercentage": attendancePercentage,
            "absenteeDays": absenteeDays,
            "riskStatus": calculate_risk_status(
                record.gpa,
                attendancePercentage if attendancePercentage is not None else 100,
                record.backlogs
            )
        })

    return jsonify({
        "student": {
            "userId": str(user.id),   # always return Mongo _id as string
            "name": profile.user.name,
            "course": profile.course,
            "year": profile.year
        },
        "dashboard": dashboard
    }), 200