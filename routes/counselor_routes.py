# routes/counselor_routes.py

from flask import Blueprint, request, jsonify
from models.counselor import Counselor, CounselorNote
from models.student import StudentProfile
from models.user import User
from routes.auth import decode_jwt  # JWT utility function
import datetime

counselor_bp = Blueprint("counselor", __name__)


# ---------- Helper ----------
def get_current_counselor():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded["role"] != "counselor":
        return None, jsonify({"message": "Unauthorized"}), 403

    # fetch the user first
    user = User.objects(userId=decoded["userId"]).first()
    if not user:
        return None, jsonify({"message": "User not found"}), 404

    counselor = Counselor.objects(user=user).first()
    if not counselor:
        return None, jsonify({"message": "Counselor profile not found"}), 404

    return counselor, None, None


@counselor_bp.route("/counselor/create-profile", methods=["POST"])
def create_counselor_profile():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    decoded = decode_jwt(token)
    if not decoded or decoded["role"] != "counselor":
        return jsonify({"message": "Unauthorized"}), 403

    user = User.objects(userId=decoded["userId"]).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if Counselor.objects(user=user).first():
        return jsonify({"message": "Counselor profile already exists"}), 400

    # ------------------------
    # Request data
    # ------------------------
    data = request.get_json() or {}
    specialization = data.get("specialization", "")
    experienceYears = data.get("experienceYears", 0)
    phone = data.get("phone", "")
    student_ids = data.get("assigned_students", [])

    # ------------------------
    # Resolve assigned students
    # ------------------------
    assigned_students = []
    for uid in student_ids:
        student_user = User.objects(userId=uid).first()
        if not student_user:
            continue

        student = StudentProfile.objects(user=student_user).first()
        if not student:
            # ✅ Auto-create StudentProfile if missing
            student = StudentProfile(user=student_user).save()

        assigned_students.append(student)

    # ------------------------
    # Create counselor
    # ------------------------
    counselor = Counselor(
        user=user,
        specialization=specialization,
        experienceYears=experienceYears,
        phone=phone,
        assigned_students=assigned_students
    ).save()

    return jsonify({
        "message": "Counselor profile created",
        "id": str(counselor.id),
        "assigned_students": [s.user.userId for s in assigned_students]
    }), 201


# ---------- Update Counselor Profile ----------
@counselor_bp.route("/counselor/update-profile", methods=["PUT"])
def update_counselor_profile():
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    data = request.get_json() or {}

    specialization = data.get("specialization")
    phone = data.get("phone")
    experienceYears = data.get("experienceYears")

    updated_fields = {}

    if specialization is not None:
        counselor.specialization = specialization
        updated_fields["specialization"] = specialization

    if phone is not None:
        counselor.phone = phone
        updated_fields["phone"] = phone

    if experienceYears is not None:
        counselor.experienceYears = experienceYears
        updated_fields["experienceYears"] = experienceYears

    counselor.updatedAt = datetime.datetime.utcnow()
    counselor.save()

    return jsonify({
        "message": "Counselor profile updated successfully",
        "updatedFields": updated_fields
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
        student_user = User.objects(userId=uid).first()
        if not student_user:
            skipped.append({"studentId": uid, "reason": "User not found"})
            continue

        student = StudentProfile.objects(user=student_user).first()
        if not student:
            skipped.append({"studentId": uid, "reason": "Student profile not found"})
            continue

        if student in counselor.assigned_students:
            skipped.append({"studentId": uid, "reason": "Already assigned"})
            continue

        # ✅ Append StudentProfile reference
        counselor.assigned_students.append(student)
        assigned.append(uid)

    counselor.updatedAt = datetime.datetime.utcnow()
    counselor.save()
    counselor.reload()   # ✅ ensures the updated list is fetched from DB

    return jsonify({
        "message": "Students assignment complete",
        "assigned": assigned,
        "skipped": skipped,
        "totalAssigned": len(assigned),
        "currentAssigned": [str(s.id) for s in counselor.assigned_students]  # ✅ debugging
    }), 200

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

    student_user = User.objects(userId=student_id).first()
    if not student_user:
        return jsonify({"message": "User not found"}), 404

    student = StudentProfile.objects(user=student_user).first()
    if not student or student not in counselor.assigned_students:
        return jsonify({"message": "Student not found or not assigned"}), 404

    notes = CounselorNote.objects(student=student, counselor=counselor)
    return jsonify({
        "student": {
            "studentId": student.user.userId,
            "name": student.user.name,
            "semester": student.semester,
            "notes": [
                {"id": str(n.id), "note": n.note, "createdAt": n.createdAt}
                for n in notes
            ]
        }
    }), 200


# ---------- Add Note ----------
@counselor_bp.route("/counselor/students/<student_id>/notes", methods=["POST"])
def add_note(student_id):
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    student_user = User.objects(userId=student_id).first()
    if not student_user:
        return jsonify({"message": "User not found"}), 404

    student = StudentProfile.objects(user=student_user).first()
    if not student or student not in counselor.assigned_students:
        return jsonify({"message": "Student not found or not assigned"}), 404

    data = request.get_json() or {}
    note_text = data.get("note")
    if not note_text:
        return jsonify({"message": "Note text required"}), 400

    note = CounselorNote(
        counselor=counselor,
        student=student,
        note=note_text
    ).save()

    return jsonify({"message": "Note added", "noteId": str(note.id)}), 201


# ---------- Get Notes ----------
@counselor_bp.route("/counselor/students/<student_id>/notes", methods=["GET"])
def get_notes(student_id):
    counselor, err_resp, code = get_current_counselor()
    if err_resp:
        return err_resp, code

    student_user = User.objects(userId=student_id).first()
    if not student_user:
        return jsonify({"message": "User not found"}), 404

    student = StudentProfile.objects(user=student_user).first()
    if not student or student not in counselor.assigned_students:
        return jsonify({"message": "Student not found or not assigned"}), 404

    notes = CounselorNote.objects(student=student, counselor=counselor)
    return jsonify({
        "notes": [
            {"id": str(n.id), "note": n.note, "createdAt": n.createdAt}
            for n in notes
        ]
    }), 200