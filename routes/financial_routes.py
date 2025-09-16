from flask import request, Blueprint, jsonify
from models.student import StudentProfile
from models.financial import FinancialRecord
from models.user import User  
import csv, io

financial_bp = Blueprint('financial', __name__)

@financial_bp.route('/financial', methods=['POST'])
def upload_financial_csv():
    file = request.files.get('file')
    if not file:
        return jsonify({"message": "No file found"}), 400

    reader = csv.DictReader(io.StringIO(file.stream.read().decode('UTF-8')))
    created_records = []

    for row in reader:
        user_obj = User.objects(userId=row["userId"]).first()
        if not user_obj:
            continue

        profile = StudentProfile.objects(user=user_obj).first()
        if not profile:
            continue

        record = FinancialRecord(
            student=profile,
            tuitionStatus=row.get('tuitionStatus', 'on-time'),
            scholarship=row.get('scholarship', "False").lower() == 'true',
            loanDependency=row.get('loanDependency', "False").lower() == 'true',
            partTimeJob=row.get('partTimeJob', 'False').lower() == 'true'
        ).save()

        created_records.append(str(record.id))

    return jsonify({
        'message': "Financial Records uploaded",
        'records': created_records
    }), 201
