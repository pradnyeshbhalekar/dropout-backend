from flask import Blueprint, request, jsonify
from models.counselor import Counselor, CounselorNote
from models.student import StudentProfile
from models.user import User
from models.academic import AcademicRecord
from models.attendance import Attendance
from routes.auth import decode_jwt  # your JWT utils
from utils.dashboard_utils import calculate_risk_status
import datetime

counselor_bp = Blueprint("counselor", __name__)


# ---------- Helper ----------
def get_current_counselor():
    """Fetch the counselor object from the JWT in the request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded.get("role") != "counselor":
        return None, jsonify({"message": "Unauthorized"}), 403

    user = User.objects(userId=str(decoded["userId"])).first()
    if not user:
        return None, jsonify({"message": "User not found"}), 404

    counselor = Counselor.objects(user=user).first()
    if not counselor:
        # Optionally: auto-create a counselor profile if needed
        counselor = Counselor(
            user=user,
            department="",
            assigned_students=[],
            createdAt=datetime.datetime.utcnow(),
            updatedAt=datetime.datetime.utcnow()
        ).save()

    return counselor, None, None


@counselor_bp.route('/counselor/profile', methods=['POST'])
def get_or_create_counselor_route():
    """Fetch current counselor from JWT or create profile if not exists"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded.get("role") != "counselor":
        return jsonify({"message": "Unauthorized"}), 403

    user_id = decoded["userId"]
    user = User.objects(userId=user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    counselor = Counselor.objects(user=user).first()
    if not counselor:
        # auto-create counselor profile
        counselor = Counselor(
            user=user,
            department="",
            assigned_students=[],
            createdAt=datetime.datetime.utcnow(),
            updatedAt=datetime.datetime.utcnow()
        ).save()

    # Convert counselor object to a dictionary for JSON response
    return jsonify({
        "message": "Counselor profile fetched or created",
        "counselor": {
            "id": str(counselor.id),
            "userId": counselor.user.userId,
            "name": counselor.user.name,
            "department": getattr(counselor, "department", ""),
            "assigned_students": [s.user.userId for s in counselor.assigned_students],
            "createdAt": counselor.createdAt,
            "updatedAt": counselor.updatedAt
        }
    }), 200




# ---------- Assign Multiple Students ----------
@counselor_bp.route("/counselor/students/assign", methods=["POST"])
def assign_multiple_students():
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    data = request.get_json() or {}
    student_ids = data.get("studentIds", [])

    if not student_ids or not isinstance(student_ids, list):
        return jsonify({"message": "studentIds must be a non-empty list"}), 400

    assigned = []
    skipped = []

    for uid in student_ids:
        user = User.objects(userId=str(uid)).first()
        if not user:
            skipped.append({"studentId": uid, "reason": "User not found"})
            continue

        student = StudentProfile.objects(user=user).first()
        if not student:
            skipped.append({"studentId": uid, "reason": "Student profile not found"})
            continue

        if any(s.id == student.id for s in counselor.assigned_students):
            skipped.append({"studentId": uid, "reason": "Already assigned"})
            continue

        counselor.assigned_students.append(student)
        # Also update student's counselor field
        student.counselor = counselor
        student.userId = student.user.userId  # Update userId field if needed
        student.save()
        
        assigned.append({
            "studentId": student.user.userId,
            "name": student.user.name
        })

    counselor.updatedAt = datetime.datetime.utcnow()
    counselor.save()

    return jsonify({
        "message": "Students assignment completed",
        "assigned": assigned,
        "skipped": skipped
    }), 201


# ---------- Get Assigned Students ----------
@counselor_bp.route("/counselor/students", methods=["GET"])
def get_assigned_students():
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    students = [
        {
            "studentId": s.user.userId,
            "name": s.user.name,
            "semester": s.semester
        } for s in counselor.assigned_students
    ]
    return jsonify({"students": students}), 200


# ---------- Get Single Student Details ----------
@counselor_bp.route("/counselor/students/<student_id>", methods=["GET"])
def get_student_details(student_id):
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    user = User.objects(userId=str(student_id)).first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    student = StudentProfile.objects(user=user).first()
    if not student or all(s.id != student.id for s in counselor.assigned_students):
        return jsonify({"message": "Student not assigned"}), 404

    notes = CounselorNote.objects(student=student, counselor=counselor)
    return jsonify({
        "student": {
            "studentId": student.user.userId,
            "name": student.user.name,
            "semester": student.semester,
            "notes": [{"id": str(n.id), "note": n.note, "createdAt": n.createdAt} for n in notes]
        }
    }), 200


# ---------- Add Note ----------
@counselor_bp.route("/counselor/students/<student_id>/notes", methods=["POST"])
def add_note(student_id):
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    user = User.objects(userId=str(student_id)).first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    student = StudentProfile.objects(user=user).first()
    if not student or all(s.id != student.id for s in counselor.assigned_students):
        return jsonify({"message": "Student not assigned"}), 404

    data = request.get_json() or {}
    note_text = data.get("note")
    if not note_text:
        return jsonify({"message": "Note text required"}), 400

    note = CounselorNote(
        counselor=counselor,
        student=student,
        note=note_text,
        createdAt=datetime.datetime.utcnow(),
        updatedAt=datetime.datetime.utcnow()
    ).save()

    return jsonify({"message": "Note added", "noteId": str(note.id)}), 201


# ---------- Get Notes ----------
@counselor_bp.route("/counselor/students/<student_id>/notes", methods=["GET"])
def get_notes(student_id):
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    user = User.objects(userId=str(student_id)).first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    student = StudentProfile.objects(user=user).first()
    if not student or all(s.id != student.id for s in counselor.assigned_students):
        return jsonify({"message": "Student not assigned"}), 404

    notes = CounselorNote.objects(student=student, counselor=counselor)
    return jsonify({
        "notes": [{"id": str(n.id), "note": n.note, "createdAt": n.createdAt} for n in notes]
    }), 200


# ---------- Counselor Dashboard - Get All Students Performance Data ----------
@counselor_bp.route("/counselor/dashboard", methods=["GET"])
def get_counselor_dashboard():
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    # Get all students assigned to this counselor from counselor's assigned_students list
    all_students = counselor.assigned_students
    
    if not all_students:
        return jsonify({
            "message": "No students assigned",
            "counselor": {
                "userId": counselor.userId or counselor.user.userId,
                "name": counselor.user.name,
                "department": counselor.department
            },
            "students": [],
            "summary": {
                "totalStudents": 0,
                "avgGpa": 0,
                "avgAttendance": 0,
                "riskDistribution": {
                    "safe": 0,
                    "warning": 0,
                    "atRisk": 0
                }
            }
        }), 200

    students_data = []
    total_gpa = 0
    total_attendance = 0
    valid_gpa_count = 0
    valid_attendance_count = 0
    risk_counts = {"safe": 0, "warning": 0, "atRisk": 0}

    for student in all_students:
        # Get latest academic record
        latest_academic = AcademicRecord.objects(student=student).order_by('-semester').first()
        
        # Get latest attendance record  
        latest_attendance = Attendance.objects(student=student).order_by('-semester').first()
        
        # Calculate current risk status
        gpa = latest_academic.gpa if latest_academic else None
        attendance_pct = latest_attendance.attendancePercentage if latest_attendance else None
        backlogs = latest_academic.backlogs if latest_academic else 0
        
        risk_status = "Unknown"
        if gpa is not None and attendance_pct is not None:
            risk_status = calculate_risk_status(gpa, attendance_pct, backlogs)
        
        # Count for summary
        if gpa is not None:
            total_gpa += gpa
            valid_gpa_count += 1
            
        if attendance_pct is not None:
            total_attendance += attendance_pct
            valid_attendance_count += 1
        
        # Risk distribution
        if risk_status == "Safe":
            risk_counts["safe"] += 1
        elif risk_status == "Warning":
            risk_counts["warning"] += 1
        elif risk_status == "At Risk":
            risk_counts["atRisk"] += 1
        
        # Get all semester records for trends
        all_academic_records = AcademicRecord.objects(student=student).order_by('semester')
        all_attendance_records = Attendance.objects(student=student).order_by('semester')
        
        # Create attendance map
        attendance_map = {att.semester: att for att in all_attendance_records}
        
        semester_records = []
        for record in all_academic_records:
            att = attendance_map.get(record.semester, None)
            semester_records.append({
                "semester": record.semester,
                "gpa": record.gpa,
                "cgpa": getattr(record, "cgpa", None),
                "backlogs": record.backlogs,
                "attendancePercentage": att.attendancePercentage if att else None,
                "absenteeDays": att.absenteeDays if att else None,
                "riskStatus": calculate_risk_status(
                    record.gpa,
                    att.attendancePercentage if att else 100,
                    record.backlogs
                )
            })
        
        student_data = {
            "studentId": student.user.userId,
            "name": student.user.name,
            "course": student.course,
            "year": student.year,
            "currentSemester": student.semester,
            "currentGpa": gpa,
            "currentAttendance": attendance_pct,
            "currentBacklogs": backlogs,
            "currentRiskStatus": risk_status,
            "semesterRecords": semester_records,
            "totalSemesters": len(semester_records)
        }
        
        students_data.append(student_data)
    
    # Calculate summary statistics
    avg_gpa = (total_gpa / valid_gpa_count) if valid_gpa_count > 0 else 0
    avg_attendance = (total_attendance / valid_attendance_count) if valid_attendance_count > 0 else 0
    
    total_students = len(students_data)
    risk_distribution = {
        "safe": round((risk_counts["safe"] / total_students) * 100, 1) if total_students > 0 else 0,
        "warning": round((risk_counts["warning"] / total_students) * 100, 1) if total_students > 0 else 0,
        "atRisk": round((risk_counts["atRisk"] / total_students) * 100, 1) if total_students > 0 else 0
    }
    
    return jsonify({
        "counselor": {
            "userId": counselor.userId or counselor.user.userId,
            "name": counselor.user.name,
            "department": counselor.department
        },
        "students": students_data,
        "summary": {
            "totalStudents": total_students,
            "avgGpa": round(avg_gpa, 2),
            "avgAttendance": round(avg_attendance, 1),
            "riskDistribution": risk_distribution,
            "riskCounts": risk_counts
        }
    }), 200


# ---------- Assign Student to Counselor (Admin endpoint) ----------
@counselor_bp.route("/admin/assign-student", methods=["POST"])
def assign_student_to_counselor():
    """Admin endpoint to assign a student to a counselor"""
    # Check if user is admin
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded.get("role") != "admin":
        return jsonify({"message": "Admin access required"}), 403

    data = request.get_json() or {}
    student_user_id = data.get("studentUserId")
    counselor_user_id = data.get("counselorUserId")
    
    if not student_user_id or not counselor_user_id:
        return jsonify({"message": "studentUserId and counselorUserId are required"}), 400
    
    # Find student
    student_user = User.objects(userId=student_user_id).first()
    if not student_user:
        return jsonify({"message": "Student user not found"}), 404
    
    student_profile = StudentProfile.objects(user=student_user).first()
    if not student_profile:
        return jsonify({"message": "Student profile not found"}), 404
    
    # Find counselor
    counselor_user = User.objects(userId=counselor_user_id).first()
    if not counselor_user:
        return jsonify({"message": "Counselor user not found"}), 404
    
    counselor = Counselor.objects(user=counselor_user).first()
    if not counselor:
        return jsonify({"message": "Counselor profile not found"}), 404
    
    # Update student profile with counselor reference
    student_profile.counselor = counselor
    student_profile.userId = student_user.userId  # Update userId field
    student_profile.save()
    
    # Update counselor's assigned students list (if not already present)
    if student_profile not in counselor.assigned_students:
        counselor.assigned_students.append(student_profile)
        counselor.userId = counselor_user.userId  # Update userId field
        counselor.updatedAt = datetime.datetime.utcnow()
        counselor.save()
    
    return jsonify({
        "message": "Student assigned to counselor successfully",
        "student": {
            "userId": student_user.userId,
            "name": student_user.name
        },
        "counselor": {
            "userId": counselor_user.userId,
            "name": counselor_user.name
        }
    }), 200
# ---------- Bulk Assign Students ----------
@counselor_bp.route("/counselor/assign-students", methods=["POST"])
def assign_students_to_self():
    """
    Counselor assigns multiple students to themselves.
    Body:
    {
        "studentIds": ["STU-6921FA35", "STU-6921FA36"]
    }
    """
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    data = request.get_json() or {}
    student_ids = data.get("studentIds", [])

    if not student_ids or not isinstance(student_ids, list):
        return jsonify({"message": "studentIds must be a non-empty list"}), 400

    assigned = []
    skipped = []

    for sid in student_ids:
        # Step 1: Get the User object
        user = User.objects(userId=sid).first()
        if not user:
            skipped.append({"studentId": sid, "reason": "User not found"})
            continue

        # Step 2: Get the StudentProfile for this User
        student_profile = StudentProfile.objects(user=user).first()
        if not student_profile:
            skipped.append({"studentId": sid, "reason": "Student profile not found"})
            continue

        # Step 3: Check if already assigned
        if any(s.id == student_profile.id for s in counselor.assigned_students):
            skipped.append({"studentId": sid, "reason": "Already assigned"})
            continue

        # Step 4: Assign student - ensure both sides are synchronized
        counselor.assigned_students.append(student_profile)
        student_profile.counselor = counselor
        student_profile.userId = user.userId  # Update userId field if needed
        student_profile.save()

        assigned.append({
            "studentId": student_profile.user.userId,
            "course": student_profile.course,
            "year": student_profile.year,
            "semester": student_profile.semester
        })

    counselor.updatedAt = datetime.datetime.utcnow()
    counselor.save()

    return jsonify({
        "message": "Students assignment completed",
        "assigned": assigned,
        "skipped": skipped
    }), 201
