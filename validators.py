import re

NAME_REGEX = re.compile(r"^[A-Za-z\s'\-]{2,60}$")
CLASS_REGEX = re.compile(r"^[A-Za-z0-9\s.\-\/]{2,50}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^[6-9]\d{9}$")  # Standard 10-digit mobile number format starting with 6-9
PHONE_ALT_REGEX = re.compile(r"^\d{10}$")

VALID_GENDERS = {'Male', 'Female', 'Other'}

def validate_name(name):
    name = (name or '').strip()
    if not name:
        return False, "Full name is required."
    if len(name) < 2:
        return False, "Name must be at least 2 characters long."
    if len(name) > 60:
        return False, "Name must not exceed 60 characters."
    if not NAME_REGEX.match(name):
        return False, "Name can only contain alphabetic letters, spaces, hyphens, and apostrophes."
    return True, ""


def validate_class(class_name):
    class_name = (class_name or '').strip()
    if not class_name:
        return False, "Class / Academic year is required."
    if len(class_name) < 2 or len(class_name) > 50:
        return False, "Class must be between 2 and 50 characters."
    if not CLASS_REGEX.match(class_name):
        return False, "Class can only contain letters, numbers, spaces, dots, hyphens, and slashes."
    return True, ""


def validate_gender(gender):
    if gender not in VALID_GENDERS:
        return False, "Please select a valid gender (Male, Female, or Other)."
    return True, ""


def validate_email(email):
    email = (email or '').strip().lower()
    if not email:
        return False, "Email address is required."
    if len(email) > 100:
        return False, "Email address must not exceed 100 characters."
    if not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address (e.g., student@university.edu)."
    return True, ""


def validate_phone(phone):
    phone = (phone or '').strip()
    if not phone:
        return False, "Phone number is required."
    if not PHONE_ALT_REGEX.match(phone):
        return False, "Phone number must be exactly 10 digits."
    # Prevent trivial repeated numbers like 0000000000, 1111111111
    if len(set(phone)) == 1:
        return False, "Please enter a valid, non-trivial 10-digit mobile number."
    return True, ""


def validate_password_strength(password):
    """
    Strong Password Requirements:
    - At least 8 characters
    - At most 128 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 number (0-9)
    - At least 1 special character (@$!%*?&#^()_-+=...)
    """
    if not password:
        return False, ["Password is required."]
    
    issues = []
    if len(password) < 8:
        issues.append("at least 8 characters")
    if len(password) > 128:
        issues.append("no more than 128 characters")
    if not re.search(r"[A-Z]", password):
        issues.append("at least one uppercase letter (A-Z)")
    if not re.search(r"[a-z]", password):
        issues.append("at least one lowercase letter (a-z)")
    if not re.search(r"\d", password):
        issues.append("at least one number (0-9)")
    if not re.search(r"[@$!%*?&#^()_\-+=\[\]{}|;:,.<>]", password):
        issues.append("at least one special symbol (@$!%*?&#...)")

    if issues:
        msg = "Password must include " + ", ".join(issues) + "."
        return False, [msg]
    return True, []


def calculate_password_score(password):
    """Returns a score from 0 to 100 and a label."""
    if not password:
        return 0, "None"
    score = 0
    if len(password) >= 8:
        score += 25
    if len(password) >= 12:
        score += 15
    if re.search(r"[A-Z]", password):
        score += 15
    if re.search(r"[a-z]", password):
        score += 15
    if re.search(r"\d", password):
        score += 15
    if re.search(r"[@$!%*?&#^()_\-+=\[\]{}|;:,.<>]", password):
        score += 15

    score = min(100, score)
    if score < 40:
        label = "Weak"
    elif score < 80:
        label = "Medium"
    else:
        label = "Strong"
    return score, label
