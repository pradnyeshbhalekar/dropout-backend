from flask import Blueprint, request, jsonify
from models.counselor import Mentor, MentorNote
from models.student import StudentProfile
from models.user import User
from routes.auth import decode_jwt  # use your JWT utils

counselor_bp = Blueprint("mentor", __name__)


# ---------- Assign Multiple Students ----------
@counselor_bp.route("/counselor/students/assign", methods=["POST"])
def assign_multiple_students():
    mentor, err_resp, code = get_current_mentor()
    if err_resp:
        return err_resp, code

    data = request.get_json() or {}
    student_ids = data.get("studentIds", [])

    if not student_ids or not isinstance(student_ids, list):
        return jsonify({"message": "studentIds must be a non-empty list"}), 400

    assigned = []
    skipped = []

    for uid in student_ids:
        student = StudentProfile.objects(user__userId=uid).first()
        if not student:
            skipped.append({"studentId": uid, "reason": "Not found"})
            continue
        if student in mentor.assigned_students:
            skipped.append({"studentId": uid, "reason": "Already assigned"})
            continue

        mentor.assigned_students.append(student)
        assigned.append({
            "studentId": student.user.userId,
            "name": student.user.name
        })

    mentor.save()

    return jsonify({
        "message": "Students assignment completed",
        "assigned": assigned,
        "skipped": skipped
    }), 201


# ---------- Helper ----------
def get_current_mentor():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, jsonify({"message": "Missing or invalid token"}), 401
    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded["role"] != "mentor":
        return None, jsonify({"message": "Unauthorized"}), 403
    mentor = Mentor.objects(user__userId=decoded["userId"]).first()
    if not mentor:
        return None, jsonify({"message": "Mentor profile not found"}), 404
    return mentor, None, None

# ---------- Get Assigned Students ----------
@counselor_bp.route("/counselor/students", methods=["GET"])
def get_assigned_students():
    mentor, err_resp, code = get_current_mentor()
    if err_resp:
        return err_resp, code
    students = [
        {
            "studentId": s.user.userId,
            "name": s.user.name,
            "semester": s.semester
        } for s in mentor.assigned_students
    ]
    return jsonify({"students": students}), 200

# ---------- Get Single Student Details ----------
@counselor_bp.route("/counselor/students/<student_id>", methods=["GET"])
def get_student_details(student_id):
    mentor, err_resp, code = get_current_mentor()
    if err_resp:
        return err_resp, code
    student = StudentProfile.objects(user__userId=student_id).first()
    if not student or student not in mentor.assigned_students:
        return jsonify({"message": "Student not found or not assigned"}), 404

    # include basic details + notes
    notes = MentorNote.objects(student=student, mentor=mentor)
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
    mentor, err_resp, code = get_current_mentor()
    if err_resp:
        return err_resp, code
    student = StudentProfile.objects(user__userId=student_id).first()
    if not student or student not in mentor.assigned_students:
        return jsonify({"message": "Student not found or not assigned"}), 404
    
    data = request.get_json() or {}
    note_text = data.get("note")
    if not note_text:
        return jsonify({"message": "Note text required"}), 400

    note = MentorNote(
        mentor=mentor,
        student=student,
        note=note_text
    ).save()

    return jsonify({"message": "Note added", "noteId": str(note.id)}), 201

@counselor_bp.route("/counselor/students/<student_id>/notes", methods=["GET"])
def get_notes(student_id):
    mentor, err_resp, code = get_current_mentor()
    if err_resp:
        return err_resp, code
    student = StudentProfile.objects(user__userId=student_id).first()
    if not student or student not in mentor.assigned_students:
        return jsonify({"message": "Student not found or not assigned"}), 404

    notes = MentorNote.objects(student=student, mentor=mentor)
    return jsonify({
        "notes": [{"id": str(n.id), "note": n.note, "createdAt": n.createdAt} for n in notes]
    }), 200