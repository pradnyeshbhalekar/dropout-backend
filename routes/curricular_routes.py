from flask import Blueprint, request, jsonify
from models.user import User
from models.student import StudentProfile
from models.curricular import CurricularUnit  # new model you added
import csv, io

curricular_bp = Blueprint('curricular', __name__)

@curricular_bp.route('/curricular', methods=['POST'])
def upload_curricular_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "No file uploaded"}), 400

    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_units = []
    skipped_rows = []

    for idx, row in enumerate(reader, start=1):
        user_id = row.get('userId')
        user_obj = User.objects(userId=user_id).first()
        if not user_obj:
            skipped_rows.append({"row": idx, "userId": user_id, "reason": "User not found"})
            continue

        profile = StudentProfile.objects(user=user_obj).first()
        if not profile:
            skipped_rows.append({"row": idx, "userId": user_id, "reason": "Student profile not found"})
            continue

        try:
            semester = int(row.get('semester', 0))
            enrolled = int(row.get('enrolled_units', 0))
            approved = int(row.get('approved_units', 0))
            grade = float(row.get('average_grade', 0))
        except ValueError as e:
            skipped_rows.append({"row": idx, "userId": user_id, "reason": f"Invalid number format: {str(e)}"})
            continue

        cu = CurricularUnit(
            student=profile,
            semester=semester,
            enrolled_units=enrolled,
            approved_units=approved,
            average_grade=grade
        ).save()

        created_units.append(str(cu.id))

    return jsonify({
        "message": "Curricular units uploaded",
        "created": created_units,
        "skipped": skipped_rows
    }), 201
