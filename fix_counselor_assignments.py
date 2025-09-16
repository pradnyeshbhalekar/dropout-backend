#!/usr/bin/env python3
"""
Script to fix counselor-student assignment synchronization.
This ensures that when a counselor has students in their assigned_students list,
those students also have the counselor properly set in their counselor field.
"""

from models.user import User
from models.student import StudentProfile
from models.counselor import Counselor
from mongoengine import connect
from config import Config

def fix_counselor_assignments():
    # Connect to database
    connect(db=Config.DB_NAME, host=Config.MONGO_URI, alias='default')
    
    print("Fixing counselor-student assignment synchronization...")
    
    counselors = Counselor.objects()
    fixed_count = 0
    
    for counselor in counselors:
        print(f"\nProcessing counselor: {counselor.user.userId} ({counselor.user.name})")
        print(f"  Assigned students in list: {len(counselor.assigned_students)}")
        
        for student in counselor.assigned_students:
            # Check if student's counselor field is set correctly
            if student.counselor != counselor:
                print(f"  Fixing student: {student.user.userId} ({student.user.name})")
                student.counselor = counselor
                student.userId = student.user.userId  # Update userId field
                student.save()
                fixed_count += 1
            else:
                print(f"  Student already correctly assigned: {student.user.userId} ({student.user.name})")
    
    print(f"\nFixed {fixed_count} student assignments.")
    
    # Verify the fix
    print("\n=== VERIFICATION ===")
    for counselor in counselors:
        print(f"Counselor: {counselor.user.userId} ({counselor.user.name})")
        students_via_field = StudentProfile.objects(counselor=counselor)
        print(f"  Students in assigned_students list: {len(counselor.assigned_students)}")
        print(f"  Students with counselor field set: {students_via_field.count()}")
        if len(counselor.assigned_students) != students_via_field.count():
            print(f"  ⚠️  MISMATCH DETECTED!")
        else:
            print(f"  ✅ Synchronized correctly")

if __name__ == "__main__":
    fix_counselor_assignments()