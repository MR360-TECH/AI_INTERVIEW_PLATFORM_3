import re
from MODULES.LAYER_1_CORE_INFRASTRUCTURE.config import ALLOWED_EXTENSIONS, ALLOWED_RESUME_EXTENSIONS

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(email and re.match(pattern, email))

def profile_is_complete(user):
    if not user or not user.gender:
        return False
    if getattr(user, 'user_type', None) == 'professional':
        return bool(user.current_designation and user.years_of_experience)
    return bool(user.education and user.course and user.semester)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_resume_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS
