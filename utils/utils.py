# utils/utils.py
from models.student import User

ROLE_PREFIX = {
    "student": "STU",
    "counselor": "CNS",
    "admin": "ADM",
}

def generate_user_id(role: str) -> str:
    """
    Simple generator: prefix + count+1 padded to 3 digits.
    NOTE: This is OK for prototype. In production use a robust generator to avoid race conditions.
    """
    prefix = ROLE_PREFIX.get(role, "USR")
    # count existing users with the role
    count = User.objects(role=role).count()
    return f"{prefix}{count + 1:03d}"

def email_in_use(email: str) -> bool:
    return bool(User.objects(email=email).first())

def userId_in_use(userId: str) -> bool:
    return bool(User.objects(userId=userId).first())
