"""
Student Monitoring Service
Monitors student metrics and detects significant changes that may indicate risk
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from models.student import StudentProfile
from models.academic import AcademicRecord
from models.attendance import Attendance
from models.financial import FinancialRecord
from models.curricular import CurricularUnit
from models.alert import RiskAssessment
from models.user import User
import statistics


class MonitoringService:
    """
    Service for monitoring student metrics and detecting changes
    """
    
    # Thresholds for triggering alerts
    THRESHOLDS = {
        'attendance': {
            'critical': 60,  # Below 60% attendance
            'warning': 75,   # Below 75% attendance
            'drop_threshold': 10  # 10% drop from previous
        },
        'gpa': {
            'critical': 2.0,  # Below 2.0 GPA
            'warning': 2.5,   # Below 2.5 GPA
            'drop_threshold': 0.5  # 0.5 point drop
        },
        'failed_courses': {
            'critical': 3,  # 3 or more failed courses
            'warning': 1    # 1 or more failed courses
        },
        'assignment_completion': {
            'critical': 50,  # Below 50% completion
            'warning': 70    # Below 70% completion
        }
    }
    
    def get_student_metrics(self, student_profile: StudentProfile) -> Dict:
        """
        Gather all current metrics for a student
        
        Args:
            student_profile: StudentProfile document
            
        Returns:
            Dictionary containing all relevant metrics
        """
        metrics = {
            'student_id': str(student_profile.id),
            'user_id': student_profile.user.userId if student_profile.user else None,
            'timestamp': datetime.utcnow()
        }
        
        # Get latest academic record
        latest_academic = AcademicRecord.objects(
            student=student_profile
        ).order_by('-semester').first()
        
        if latest_academic:
            metrics['current_gpa'] = latest_academic.gpa
            metrics['current_semester'] = latest_academic.semester
            metrics['backlogs'] = latest_academic.backlogs
        
        # Get latest attendance
        latest_attendance = Attendance.objects(
            student=student_profile
        ).order_by('-semester').first()
        
        if latest_attendance:
            metrics['attendance_percentage'] = latest_attendance.attendancePercentage
            metrics['absent_days'] = latest_attendance.absenteeDays
        
        # Get financial status
        financial_record = FinancialRecord.objects(
            student=student_profile
        ).first()
        
        if financial_record:
            metrics['tuition_status'] = financial_record.tuitionStatus
            metrics['scholarship'] = financial_record.scholarship
            metrics['loan_dependency'] = financial_record.loanDependency
        
        # Get curricular units
        latest_curricular = CurricularUnit.objects(
            student=student_profile
        ).order_by('-semester').first()
        
        if latest_curricular:
            metrics['enrolled_units'] = latest_curricular.enrolled_units
            metrics['approved_units'] = latest_curricular.approved_units
            metrics['average_grade'] = latest_curricular.average_grade
            metrics['completion_rate'] = (
                latest_curricular.approved_units / latest_curricular.enrolled_units * 100
                if latest_curricular.enrolled_units > 0 else 0
            )
        
        # Add profile information
        metrics['age_at_enrollment'] = student_profile.age_at_enrollment
        metrics['gender'] = student_profile.gender
        metrics['course'] = student_profile.course
        metrics['year'] = student_profile.year
        metrics['semester'] = student_profile.semester
        metrics['session_type'] = student_profile.session_type
        metrics['special_needs'] = student_profile.special_needs
        metrics['first_gen_student'] = student_profile.firstGenStudent
        metrics['background'] = student_profile.background
        
        return metrics
    
    def detect_attendance_drop(self, student_profile: StudentProfile) -> Optional[Dict]:
        """
        Detect significant drops in attendance
        
        Returns:
            Alert data if drop detected, None otherwise
        """
        # Get attendance records for last two semesters
        attendance_records = Attendance.objects(
            student=student_profile
        ).order_by('-semester').limit(2)
        
        if len(attendance_records) < 1:
            return None
        
        current_attendance = attendance_records[0].attendancePercentage
        alert_data = None
        
        # Check against critical threshold
        if current_attendance < self.THRESHOLDS['attendance']['critical']:
            alert_data = {
                'type': 'attendance_drop',
                'severity': 'critical',
                'current_value': current_attendance,
                'threshold': self.THRESHOLDS['attendance']['critical'],
                'message': f"Critical: Attendance has dropped to {current_attendance}%"
            }
        # Check against warning threshold
        elif current_attendance < self.THRESHOLDS['attendance']['warning']:
            alert_data = {
                'type': 'attendance_drop',
                'severity': 'high',
                'current_value': current_attendance,
                'threshold': self.THRESHOLDS['attendance']['warning'],
                'message': f"Warning: Attendance is at {current_attendance}%"
            }
        
        # Check for significant drop from previous semester
        if len(attendance_records) == 2:
            previous_attendance = attendance_records[1].attendancePercentage
            drop = previous_attendance - current_attendance
            
            if drop >= self.THRESHOLDS['attendance']['drop_threshold']:
                if not alert_data or alert_data['severity'] != 'critical':
                    alert_data = {
                        'type': 'attendance_drop',
                        'severity': 'high' if drop >= 15 else 'medium',
                        'current_value': current_attendance,
                        'previous_value': previous_attendance,
                        'drop': drop,
                        'message': f"Attendance dropped by {drop}% from last semester"
                    }
        
        return alert_data
    
    def detect_gpa_drop(self, student_profile: StudentProfile) -> Optional[Dict]:
        """
        Detect significant drops in GPA
        
        Returns:
            Alert data if drop detected, None otherwise
        """
        # Get academic records for last two semesters
        academic_records = AcademicRecord.objects(
            student=student_profile
        ).order_by('-semester').limit(2)
        
        if len(academic_records) < 1:
            return None
        
        current_gpa = academic_records[0].gpa
        alert_data = None
        
        # Check against critical threshold
        if current_gpa < self.THRESHOLDS['gpa']['critical']:
            alert_data = {
                'type': 'gpa_drop',
                'severity': 'critical',
                'current_value': current_gpa,
                'threshold': self.THRESHOLDS['gpa']['critical'],
                'message': f"Critical: GPA has dropped to {current_gpa:.2f}"
            }
        # Check against warning threshold
        elif current_gpa < self.THRESHOLDS['gpa']['warning']:
            alert_data = {
                'type': 'gpa_drop',
                'severity': 'high',
                'current_value': current_gpa,
                'threshold': self.THRESHOLDS['gpa']['warning'],
                'message': f"Warning: GPA is at {current_gpa:.2f}"
            }
        
        # Check for significant drop from previous semester
        if len(academic_records) == 2:
            previous_gpa = academic_records[1].gpa
            drop = previous_gpa - current_gpa
            
            if drop >= self.THRESHOLDS['gpa']['drop_threshold']:
                if not alert_data or alert_data['severity'] != 'critical':
                    alert_data = {
                        'type': 'gpa_drop',
                        'severity': 'high' if drop >= 0.7 else 'medium',
                        'current_value': current_gpa,
                        'previous_value': previous_gpa,
                        'drop': drop,
                        'message': f"GPA dropped by {drop:.2f} points from last semester"
                    }
        
        return alert_data
    
    def detect_failed_courses(self, student_profile: StudentProfile) -> Optional[Dict]:
        """
        Detect failed courses and backlogs
        
        Returns:
            Alert data if failures detected, None otherwise
        """
        latest_academic = AcademicRecord.objects(
            student=student_profile
        ).order_by('-semester').first()
        
        if not latest_academic:
            return None
        
        backlogs = latest_academic.backlogs
        
        if backlogs >= self.THRESHOLDS['failed_courses']['critical']:
            return {
                'type': 'failed_course',
                'severity': 'critical',
                'value': backlogs,
                'threshold': self.THRESHOLDS['failed_courses']['critical'],
                'message': f"Critical: {backlogs} courses failed/pending"
            }
        elif backlogs >= self.THRESHOLDS['failed_courses']['warning']:
            return {
                'type': 'failed_course',
                'severity': 'high',
                'value': backlogs,
                'threshold': self.THRESHOLDS['failed_courses']['warning'],
                'message': f"Warning: {backlogs} course(s) failed/pending"
            }
        
        return None
    
    def detect_assignment_issues(self, student_profile: StudentProfile) -> Optional[Dict]:
        """
        Detect issues with assignment submissions
        
        Returns:
            Alert data if issues detected, None otherwise
        """
        latest_curricular = CurricularUnit.objects(
            student=student_profile
        ).order_by('-semester').first()
        
        if not latest_curricular:
            return None
        
        # Calculate completion rate
        if latest_curricular.enrolled_units > 0:
            completion_rate = (
                latest_curricular.approved_units / latest_curricular.enrolled_units * 100
            )
        else:
            return None
        
        if completion_rate < self.THRESHOLDS['assignment_completion']['critical']:
            return {
                'type': 'assignment_missing',
                'severity': 'critical',
                'value': completion_rate,
                'enrolled': latest_curricular.enrolled_units,
                'approved': latest_curricular.approved_units,
                'threshold': self.THRESHOLDS['assignment_completion']['critical'],
                'message': f"Critical: Only {completion_rate:.1f}% of enrolled units approved"
            }
        elif completion_rate < self.THRESHOLDS['assignment_completion']['warning']:
            return {
                'type': 'assignment_missing',
                'severity': 'medium',
                'value': completion_rate,
                'enrolled': latest_curricular.enrolled_units,
                'approved': latest_curricular.approved_units,
                'threshold': self.THRESHOLDS['assignment_completion']['warning'],
                'message': f"Warning: {completion_rate:.1f}% of enrolled units approved"
            }
        
        return None
    
    def detect_financial_issues(self, student_profile: StudentProfile) -> Optional[Dict]:
        """
        Detect financial issues that may impact retention
        
        Returns:
            Alert data if issues detected, None otherwise
        """
        financial_record = FinancialRecord.objects(
            student=student_profile
        ).first()
        
        if not financial_record:
            return None
        
        if financial_record.tuitionStatus == 'delayed':
            return {
                'type': 'financial_issue',
                'severity': 'medium',
                'issue': 'tuition_delayed',
                'has_scholarship': financial_record.scholarship,
                'loan_dependency': financial_record.loanDependency,
                'message': "Tuition payment is delayed - financial assistance may be needed"
            }
        
        return None
    
    def compare_risk_levels(self, current_risk: str, previous_risk: str) -> Optional[Dict]:
        """
        Compare risk levels and detect changes
        
        Returns:
            Alert data if significant change detected, None otherwise
        """
        risk_values = {'low': 1, 'medium': 2, 'high': 3}
        
        if not previous_risk:
            return None
        
        current_val = risk_values.get(current_risk, 0)
        previous_val = risk_values.get(previous_risk, 0)
        
        if current_val > previous_val:
            severity = 'high' if current_risk == 'high' else 'medium'
            return {
                'type': 'risk_level_change',
                'severity': severity,
                'current_risk': current_risk,
                'previous_risk': previous_risk,
                'direction': 'increased',
                'message': f"Risk level increased from {previous_risk} to {current_risk}"
            }
        elif current_val < previous_val:
            # Positive change - send encouragement
            return {
                'type': 'positive_feedback',
                'severity': 'low',
                'current_risk': current_risk,
                'previous_risk': previous_risk,
                'direction': 'decreased',
                'message': f"Great progress! Risk level decreased from {previous_risk} to {current_risk}"
            }
        
        return None
    
    def analyze_trends(self, student_profile: StudentProfile, 
                      lookback_semesters: int = 3) -> Dict:
        """
        Analyze trends in student performance over time
        
        Args:
            student_profile: StudentProfile document
            lookback_semesters: Number of semesters to analyze
            
        Returns:
            Dictionary containing trend analysis
        """
        trends = {
            'attendance_trend': 'stable',
            'gpa_trend': 'stable',
            'completion_trend': 'stable'
        }
        
        # Analyze attendance trend
        attendance_records = Attendance.objects(
            student=student_profile
        ).order_by('-semester').limit(lookback_semesters)
        
        if len(attendance_records) >= 2:
            attendance_values = [r.attendancePercentage for r in attendance_records]
            attendance_values.reverse()  # Chronological order
            
            # Simple linear trend
            if len(attendance_values) >= 2:
                trend = (attendance_values[-1] - attendance_values[0]) / len(attendance_values)
                if trend < -2:
                    trends['attendance_trend'] = 'declining'
                elif trend > 2:
                    trends['attendance_trend'] = 'improving'
        
        # Analyze GPA trend
        academic_records = AcademicRecord.objects(
            student=student_profile
        ).order_by('-semester').limit(lookback_semesters)
        
        if len(academic_records) >= 2:
            gpa_values = [r.gpa for r in academic_records if r.gpa is not None]
            gpa_values.reverse()  # Chronological order
            
            if len(gpa_values) >= 2:
                trend = (gpa_values[-1] - gpa_values[0]) / len(gpa_values)
                if trend < -0.1:
                    trends['gpa_trend'] = 'declining'
                elif trend > 0.1:
                    trends['gpa_trend'] = 'improving'
        
        # Analyze course completion trend
        curricular_records = CurricularUnit.objects(
            student=student_profile
        ).order_by('-semester').limit(lookback_semesters)
        
        if len(curricular_records) >= 2:
            completion_rates = [
                (r.approved_units / r.enrolled_units * 100) if r.enrolled_units > 0 else 0
                for r in curricular_records
            ]
            completion_rates.reverse()  # Chronological order
            
            if len(completion_rates) >= 2:
                trend = (completion_rates[-1] - completion_rates[0]) / len(completion_rates)
                if trend < -5:
                    trends['completion_trend'] = 'declining'
                elif trend > 5:
                    trends['completion_trend'] = 'improving'
        
        return trends
    
    def get_monitoring_summary(self, student_profile: StudentProfile) -> Dict:
        """
        Get a comprehensive monitoring summary for a student
        
        Args:
            student_profile: StudentProfile document
            
        Returns:
            Dictionary containing all monitoring data
        """
        summary = {
            'student_id': str(student_profile.id),
            'metrics': self.get_student_metrics(student_profile),
            'alerts': [],
            'trends': self.analyze_trends(student_profile)
        }
        
        # Check for various issues
        attendance_alert = self.detect_attendance_drop(student_profile)
        if attendance_alert:
            summary['alerts'].append(attendance_alert)
        
        gpa_alert = self.detect_gpa_drop(student_profile)
        if gpa_alert:
            summary['alerts'].append(gpa_alert)
        
        failed_courses_alert = self.detect_failed_courses(student_profile)
        if failed_courses_alert:
            summary['alerts'].append(failed_courses_alert)
        
        assignment_alert = self.detect_assignment_issues(student_profile)
        if assignment_alert:
            summary['alerts'].append(assignment_alert)
        
        financial_alert = self.detect_financial_issues(student_profile)
        if financial_alert:
            summary['alerts'].append(financial_alert)
        
        # Determine overall status
        if any(alert['severity'] == 'critical' for alert in summary['alerts']):
            summary['overall_status'] = 'critical'
        elif any(alert['severity'] == 'high' for alert in summary['alerts']):
            summary['overall_status'] = 'warning'
        elif summary['alerts']:
            summary['overall_status'] = 'attention_needed'
        else:
            summary['overall_status'] = 'good'
        
        return summary


# Singleton instance
monitoring_service = MonitoringService()