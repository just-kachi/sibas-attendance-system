from utils.db import fetch_one
from utils.security import verify_password


def authenticate_user(username_or_email: str, password: str):
    """
    Authenticates a user using username/email and password.

    Returns user details if login is successful.
    Returns None if login fails.
    """

    query = """
        SELECT
            u.user_id,
            u.username,
            u.email,
            u.password_hash,
            u.is_active,
            r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.username = %s OR u.email = %s
    """

    user = fetch_one(query, (username_or_email, username_or_email))

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "email": user["email"],
        "role_name": user["role_name"],
    }


def get_student_profile(user_id: int):
    """
    Gets the student profile connected to a user account.
    """
    query = """
        SELECT
            s.student_id,
            s.matric_no,
            s.first_name,
            s.middle_name,
            s.last_name,
            s.email,
            s.level,
            d.department_name,
            p.programme_name
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        JOIN programmes p ON s.programme_id = p.programme_id
        WHERE s.user_id = %s
    """

    return fetch_one(query, (user_id,))


def get_lecturer_profile(user_id: int):
    """
    Gets the lecturer profile connected to a user account.
    """
    query = """
        SELECT
            l.lecturer_id,
            l.staff_no,
            l.first_name,
            l.last_name,
            l.email,
            l.phone_number,
            d.department_name
        FROM lecturers l
        JOIN departments d ON l.department_id = d.department_id
        WHERE l.user_id = %s
    """

    return fetch_one(query, (user_id,))


def get_admin_profile(user_id: int):
    """
    Gets the administrator profile connected to a user account.
    Returns None if no administrator profile exists yet.
    """
    query = """
        SELECT
            admin_id,
            first_name,
            last_name,
            phone_number
        FROM administrators
        WHERE user_id = %s
    """

    return fetch_one(query, (user_id,))