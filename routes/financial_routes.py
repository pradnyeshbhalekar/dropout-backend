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
            scholarship=row.get('scholarShip', "False").lower() == 'true',
            loanDependency=row.get('loanDependency', "False").lower() == 'true',
            partTimeJob=row.get('partTimeJob', 'False').lower() == 'true'
        ).save()

        created_records.append(str(record.id))

    return jsonify({
        'message': "Financial Records uploaded",
        'records': created_records
    }), 201
    
# ✅ Get financial details for a specific student
@financial_bp.route('/financial/<userId>', methods=['GET'])
def get_financial_details(userId):
    user = User.objects(userId=userId).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = StudentProfile.objects(user=user).first()
    if not profile:
        return jsonify({"message": "Student profile not found"}), 404

    record = FinancialRecord.objects(student=profile).first()
    if not record:
        return jsonify({"message": "Financial record not found"}), 404

    return jsonify({
        "userId": userId,
        "tuitionStatus": record.tuitionStatus,
        "scholarship": record.scholarship,
        "loanDependency": record.loanDependency,
        "partTimeJob": record.partTimeJob
    }), 200


# ✅ Filter students (loan dependency or scholarship)
@financial_bp.route('/financial', methods=['GET'])
def filter_financial_records():
    loan_dependency = request.args.get("loanDependency")
    scholarship = request.args.get("scholarship")

    query = {}
    if loan_dependency is not None:
        query["loanDependency"] = loan_dependency.lower() == "true"
    if scholarship is not None:
        query["scholarship"] = scholarship.lower() == "true"

    records = FinancialRecord.objects(**query)
    data = [
        {
            "userId": r.student.user.userId,
            "tuitionStatus": r.tuitionStatus,
            "scholarship": r.scholarship,
            "loanDependency": r.loanDependency,
            "partTimeJob": r.partTimeJob
        } for r in records
    ]

    return jsonify({"results": data}), 200
