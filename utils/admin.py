from utils.db import fetch_all, fetch_one, execute_query, execute_query_returning_id
from utils.security import hash_password


def get_departments():
    query = """
        SELECT department_id, department_name, department_code
        FROM departments
        ORDER BY department_name
    """
    return fetch_all(query)


def get_programmes():
    query = """
        SELECT programme_id, programme_name, programme_code, department_id
        FROM programmes
        ORDER BY programme_name
    """
    return fetch_all(query)


def get_courses_for_admin():
    query = """
        SELECT course_id, course_code, course_title
        FROM courses
        ORDER BY course_code
    """
    return fetch_all(query)


def username_or_email_exists(username: str, email: str):
    query = """
        SELECT user_id
        FROM users
        WHERE username = %s OR email = %s
    """
    return fetch_one(query, (username, email)) is not None


def matric_no_exists(matric_no: str):
    query = """
        SELECT student_id
        FROM students
        WHERE matric_no = %s
    """
    return fetch_one(query, (matric_no,)) is not None


def create_student(
    username: str,
    email: str,
    password: str,
    matric_no: str,
    first_name: str,
    middle_name: str,
    last_name: str,
    department_id: int,
    programme_id: int,
    level: int,
    course_ids: list,
    academic_session: str,
    semester: str,
):
    """
    Creates a student user account, student profile, and course enrollments.
    """

    if username_or_email_exists(username, email):
        raise ValueError("Username or email already exists.")

    if matric_no_exists(matric_no):
        raise ValueError("Matric number already exists.")

    if not course_ids:
        raise ValueError("Please assign the student to at least one course.")

    role_query = """
        SELECT role_id
        FROM roles
        WHERE role_name = 'Student'
    """
    role = fetch_one(role_query)

    if role is None:
        raise ValueError("Student role does not exist.")

    password_hash = hash_password(password)

    user_query = """
        INSERT INTO users (role_id, username, email, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING user_id
    """

    user_id = execute_query_returning_id(
        user_query,
        (
            role["role_id"],
            username,
            email,
            password_hash,
        ),
    )

    student_query = """
        INSERT INTO students (
            user_id,
            department_id,
            programme_id,
            matric_no,
            first_name,
            middle_name,
            last_name,
            email,
            level
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING student_id
    """

    student_id = execute_query_returning_id(
        student_query,
        (
            user_id,
            department_id,
            programme_id,
            matric_no,
            first_name,
            middle_name,
            last_name,
            email,
            level,
        ),
    )

    for course_id in course_ids:
        enrollment_query = """
            INSERT INTO course_enrollments (
                student_id,
                course_id,
                academic_session,
                semester
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (student_id, course_id, academic_session, semester)
            DO NOTHING
        """

        execute_query(
            enrollment_query,
            (
                student_id,
                course_id,
                academic_session,
                semester,
            ),
        )

    return student_id

def create_department(department_name: str, department_code: str):
    """
    Creates a new department.
    """

    query = """
        INSERT INTO departments (department_name, department_code)
        VALUES (%s, %s)
    """

    execute_query(query, (department_name, department_code))


def create_programme(department_id: int, programme_name: str, programme_code: str):
    """
    Creates a new programme under a department.
    """

    query = """
        INSERT INTO programmes (department_id, programme_name, programme_code)
        VALUES (%s, %s, %s)
    """

    execute_query(query, (department_id, programme_name, programme_code))


def create_course(
    department_id: int,
    course_code: str,
    course_title: str,
    credit_units: int,
    level: int,
):
    """
    Creates a new course.
    """

    query = """
        INSERT INTO courses (
            department_id,
            course_code,
            course_title,
            credit_units,
            level
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    execute_query(
        query,
        (
            department_id,
            course_code,
            course_title,
            credit_units,
            level,
        ),
    )

def staff_no_exists(staff_no: str):
    """
    Checks whether a lecturer staff number already exists.
    """
    query = """
        SELECT lecturer_id
        FROM lecturers
        WHERE staff_no = %s
    """

    result = fetch_one(query, (staff_no,))
    return result is not None


def create_lecturer(
    username: str,
    email: str,
    password: str,
    staff_no: str,
    first_name: str,
    last_name: str,
    phone_number: str,
    department_id: int,
):
    """
    Creates a lecturer user account and lecturer profile.
    """

    if username_or_email_exists(username, email):
        raise ValueError("Username or email already exists.")

    if staff_no_exists(staff_no):
        raise ValueError("Staff number already exists.")

    role_query = """
        SELECT role_id
        FROM roles
        WHERE role_name = 'Lecturer'
    """

    role = fetch_one(role_query)

    if role is None:
        raise ValueError("Lecturer role does not exist.")

    password_hash = hash_password(password)

    user_query = """
        INSERT INTO users (role_id, username, email, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING user_id
    """

    user_id = execute_query_returning_id(
        user_query,
        (
            role["role_id"],
            username,
            email,
            password_hash,
        ),
    )

    lecturer_query = """
        INSERT INTO lecturers (
            user_id,
            department_id,
            staff_no,
            first_name,
            last_name,
            email,
            phone_number
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    execute_query(
        lecturer_query,
        (
            user_id,
            department_id,
            staff_no,
            first_name,
            last_name,
            email,
            phone_number,
        ),
    )

    return user_id


def get_lecturer_users():
    """
    Returns all users who have the Lecturer role.
    """
    query = """
        SELECT
            u.user_id,
            u.username,
            u.email,
            l.lecturer_id,
            l.staff_no,
            l.first_name,
            l.last_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        JOIN lecturers l ON u.user_id = l.user_id
        WHERE r.role_name = 'Lecturer'
        ORDER BY l.first_name, l.last_name
    """

    return fetch_all(query)


def assign_lecturer_to_course(
    lecturer_user_id: int,
    course_id: int,
    academic_session: str,
    semester: str,
):
    """
    Assigns a lecturer to a course.
    """

    lecturer_query = """
        SELECT lecturer_id
        FROM lecturers
        WHERE user_id = %s
    """

    lecturer = fetch_one(lecturer_query, (lecturer_user_id,))

    if lecturer is None:
        raise ValueError("Lecturer profile not found for this user.")

    insert_query = """
        INSERT INTO lecturer_courses (
            lecturer_id,
            course_id,
            academic_session,
            semester
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (lecturer_id, course_id, academic_session, semester)
        DO NOTHING
    """

    execute_query(
        insert_query,
        (
            lecturer["lecturer_id"],
            course_id,
            academic_session,
            semester,
        ),
    )

def get_all_lecturers():
    """
    Returns all lecturers with their department and user account details.
    """
    query = """
        SELECT
            l.lecturer_id,
            u.user_id,
            u.username,
            u.email AS login_email,
            u.is_active,
            l.staff_no,
            l.first_name,
            l.last_name,
            l.email,
            l.phone_number,
            d.department_name,
            d.department_code
        FROM lecturers l
        JOIN users u ON l.user_id = u.user_id
        JOIN departments d ON l.department_id = d.department_id
        ORDER BY l.lecturer_id
    """

    return fetch_all(query)


def get_lecturer_course_assignments():
    """
    Returns lecturer-course assignments.
    """
    query = """
        SELECT
            lc.lecturer_course_id,
            l.lecturer_id,
            l.staff_no,
            l.first_name,
            l.last_name,
            c.course_code,
            c.course_title,
            lc.academic_session,
            lc.semester
        FROM lecturer_courses lc
        JOIN lecturers l ON lc.lecturer_id = l.lecturer_id
        JOIN courses c ON lc.course_id = c.course_id
        ORDER BY l.last_name, c.course_code
    """

    return fetch_all(query)


def update_lecturer(
    lecturer_id: int,
    username: str,
    login_email: str,
    staff_no: str,
    first_name: str,
    last_name: str,
    lecturer_email: str,
    phone_number: str,
    department_id: int,
):
    """
    Updates lecturer profile and linked user account.
    """

    lecturer_query = """
        SELECT user_id
        FROM lecturers
        WHERE lecturer_id = %s
    """

    lecturer = fetch_one(lecturer_query, (lecturer_id,))

    if lecturer is None:
        raise ValueError("Lecturer not found.")

    user_id = lecturer["user_id"]

    user_update_query = """
        UPDATE users
        SET username = %s,
            email = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
    """

    execute_query(
        user_update_query,
        (
            username,
            login_email,
            user_id,
        ),
    )

    lecturer_update_query = """
        UPDATE lecturers
        SET department_id = %s,
            staff_no = %s,
            first_name = %s,
            last_name = %s,
            email = %s,
            phone_number = %s
        WHERE lecturer_id = %s
    """

    execute_query(
        lecturer_update_query,
        (
            department_id,
            staff_no,
            first_name,
            last_name,
            lecturer_email,
            phone_number,
            lecturer_id,
        ),
    )

def update_student(
    student_id: int,
    username: str,
    login_email: str,
    matric_no: str,
    first_name: str,
    middle_name: str,
    last_name: str,
    student_email: str,
    department_id: int,
    programme_id: int,
    level: int,
):
    """
    Updates student profile and linked user account.
    """

    student_query = """
        SELECT user_id
        FROM students
        WHERE student_id = %s
    """

    student = fetch_one(student_query, (student_id,))

    if student is None:
        raise ValueError("Student not found.")

    user_id = student["user_id"]

    user_update_query = """
        UPDATE users
        SET username = %s,
            email = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = %s
    """

    execute_query(
        user_update_query,
        (
            username,
            login_email,
            user_id,
        ),
    )

    student_update_query = """
        UPDATE students
        SET department_id = %s,
            programme_id = %s,
            matric_no = %s,
            first_name = %s,
            middle_name = %s,
            last_name = %s,
            email = %s,
            level = %s
        WHERE student_id = %s
    """

    execute_query(
        student_update_query,
        (
            department_id,
            programme_id,
            matric_no,
            first_name,
            middle_name,
            last_name,
            student_email,
            level,
            student_id,
        ),
    )


def get_student_course_ids(student_id: int, academic_session: str, semester: str):
    """
    Returns active course IDs currently assigned to a student.
    """

    query = """
        SELECT course_id
        FROM course_enrollments
        WHERE student_id = %s
          AND academic_session = %s
          AND semester = %s
          AND is_active = TRUE
    """

    rows = fetch_all(query, (student_id, academic_session, semester))
    return [row["course_id"] for row in rows]


def update_student_course_enrollments(
    student_id: int,
    course_ids: list,
    academic_session: str,
    semester: str,
):
    """
    Updates a student's course enrollments for a session/semester.
    """

    if not course_ids:
        raise ValueError("Please assign the student to at least one course.")

    deactivate_query = """
        UPDATE course_enrollments
        SET is_active = FALSE
        WHERE student_id = %s
          AND academic_session = %s
          AND semester = %s
    """

    execute_query(
        deactivate_query,
        (
            student_id,
            academic_session,
            semester,
        ),
    )

    for course_id in course_ids:
        insert_query = """
            INSERT INTO course_enrollments (
                student_id,
                course_id,
                academic_session,
                semester,
                is_active
            )
            VALUES (%s, %s, %s, %s, TRUE)
            ON CONFLICT (student_id, course_id, academic_session, semester)
            DO UPDATE SET is_active = TRUE
        """

        execute_query(
            insert_query,
            (
                student_id,
                course_id,
                academic_session,
                semester,
            ),
        )