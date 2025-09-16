import uuid
from models.user import User
# utils/utils.py
import uuid
from models.user import User

ROLE_PREFIX = {
    "student": "STU",
    "counselor": "CNS",
    "admin": "ADM",
}

def generate_user_id(role: str) -> str:
    """
    Generate userId using role prefix + short UUID.
    Example: STU-3f9c1a2b
    """
    prefix = ROLE_PREFIX.get(role, "USR")
    # take first 8 chars of UUID4 for uniqueness but keep it short
    unique_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{unique_part}"

def email_in_use(email: str) -> bool:
    return bool(User.objects(email=email).first())

def userId_in_use(userId: str) -> bool:
    return bool(User.objects(userId=userId).first())
