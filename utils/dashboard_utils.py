# utils/dashboard_utils.py

def calculate_risk_status(gpa, attendance, backlogs):
    if gpa >= 7.0 and attendance >= 75 and backlogs == 0:
        return "Safe"
    elif 5.0 <= gpa < 7.0 or 65 <= attendance < 75 or 1 <= backlogs <= 2:
        return "Warning"
    else:
        return "At Risk"