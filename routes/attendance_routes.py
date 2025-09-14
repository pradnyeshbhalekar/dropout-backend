from flask import request, Blueprint, jsonify
from models.attendance import Attendance
from models.student import StudentProfile
from models.user import User
import csv, io

attendance_bp = Blueprint('attendance', __name__)

#working
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
# ✅ Fetch attendance history for a student
#working
@attendance_bp.route('/attendance/record/<userId>', methods=['GET'])
def get_attendance_history(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    records = Attendance.objects(student=profile).order_by("semester")
    data = [
        {
            "semester": r.semester,
            "attendancePercentage": r.attendancePercentage,
            "absenteeDays": r.absenteeDays
        } for r in records
    ]

    return jsonify({
        "userId": userId,
        "attendanceHistory": data
    }), 200

#doubtful
# ✅ Attendance summary (per semester + overall)
@attendance_bp.route('/attendance/summary/<userId>', methods=['GET'])
def get_attendance_summary(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    records = Attendance.objects(student=profile)
    if not records:
        return jsonify({"message": "No attendance records found"}), 404

    total_percent = sum([r.attendancePercentage for r in records])
    avg_attendance = round(total_percent / len(records), 2)
    total_absentees = sum([r.absenteeDays for r in records])

    per_semester = {r.semester: r.attendancePercentage for r in records}

    return jsonify({
        "userId": userId,
        "averageAttendance": avg_attendance,
        "attendancePerSemester": per_semester,
        "totalAbsenteeDays": total_absentees
    }), 200


# ✅ Filter students by low attendance
#working
@attendance_bp.route('/attendance/defaulters', methods=['GET'])
def filter_low_attendance():
    low_attendance = request.args.get("low_attendance", type=float)
    if not low_attendance:
        return jsonify({"message": "Please provide low_attendance parameter"}), 400

    records = Attendance.objects(attendancePercentage__lt=low_attendance)
    results = [
        {
            "userId": r.student.user.userId,
            "semester": r.semester,
            "attendancePercentage": r.attendancePercentage,
            "absenteeDays": r.absenteeDays
        } for r in records
    ]

    return jsonify({
        "threshold": low_attendance,
        "students": results
    }), 200