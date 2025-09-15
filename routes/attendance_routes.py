from flask import request, Blueprint, jsonify
from models.attendance import Attendance
from models.student import StudentProfile
from models.user import User
import csv, io

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance', methods=['POST'])
def upload_attendance_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "File not found"}), 400

    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_attendance = []
    skipped_rows = []

    for idx, row in enumerate(reader, start=1):
        user_id = row.get("userId")
        user_obj = User.objects(userId=user_id).first()
        if not user_obj:
            skipped_rows.append({
                "row": idx,
                "userId": user_id,
                "reason": "User not found"
            })
            continue

        profile = StudentProfile.objects(user=user_obj).first()
        if not profile:
            skipped_rows.append({
                "row": idx,
                "userId": user_id,
                "reason": "Student profile not found"
            })
            continue

        try:
            attendance_percent = float(row.get("attendancePercentage", 0))
            absentee_days = int(row.get("absenteeDays", 0))
            semester = int(row.get("semester", 0))
        except ValueError as e:
            skipped_rows.append({
                "row": idx,
                "userId": user_id,
                "reason": f"Invalid number format: {str(e)}"
            })
            continue

        attendance = Attendance(
            student=profile,
            semester=semester,
            attendancePercentage=attendance_percent,  
            absenteeDays=absentee_days
        ).save()

        created_attendance.append(str(attendance.id))

    return jsonify({
        "message": "Attendance upload finished",
        "created": created_attendance,
        "skipped": skipped_rows
    }), 201
