import os
import sys
import pandas as pd
import psycopg2
import bcrypt


DB_NAME = "sibas_db"
DB_USER = "postgres"
DB_PASSWORD = "kachi123"
DB_HOST = "localhost"
DB_PORT = "5432"


# ============================================================
# FILE PATH
# This points to uploads/sample_students.csv
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "uploads", "sample_students.csv")


REQUIRED_COLUMNS = [
    "username",
    "email",
    "password",
    "matric_no",
    "first_name",
    "middle_name",
    "last_name",
    "department_code",
    "programme_code",
    "level",
    "course_codes",
]


def get_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def validate_csv(df: pd.DataFrame):
    """Validate that the CSV file has all required columns."""
    missing_columns = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def get_role_id(cursor, role_name: str):
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name = %s",
        (role_name,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Role '{role_name}' does not exist in roles table.")

    return result[0]


def get_department_id(cursor, department_code: str):
    cursor.execute(
        "SELECT department_id FROM departments WHERE department_code = %s",
        (department_code,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Department code '{department_code}' does not exist.")

    return result[0]


def get_programme_id(cursor, programme_code: str):
    cursor.execute(
        "SELECT programme_id FROM programmes WHERE programme_code = %s",
        (programme_code,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Programme code '{programme_code}' does not exist.")

    return result[0]


def get_course_id(cursor, course_code: str):
    cursor.execute(
        "SELECT course_id FROM courses WHERE course_code = %s",
        (course_code,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Course code '{course_code}' does not exist.")

    return result[0]


def student_exists(cursor, matric_no: str, email: str, username: str):
    """Check whether student/user already exists."""
    cursor.execute(
        """
        SELECT 1
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.matric_no = %s OR s.email = %s OR u.username = %s
        """,
        (matric_no, email, username),
    )
    return cursor.fetchone() is not None


def create_student_from_row(cursor, row, student_role_id):
    """Create a user, student profile, and course enrollments from one CSV row."""

    username = str(row["username"]).strip()
    email = str(row["email"]).strip()
    plain_password = str(row["password"]).strip()
    matric_no = str(row["matric_no"]).strip()
    first_name = str(row["first_name"]).strip()
    middle_name = "" if pd.isna(row["middle_name"]) else str(row["middle_name"]).strip()
    last_name = str(row["last_name"]).strip()
    department_code = str(row["department_code"]).strip()
    programme_code = str(row["programme_code"]).strip()
    level = int(row["level"])
    course_codes = str(row["course_codes"]).strip()

    if student_exists(cursor, matric_no, email, username):
        raise ValueError(
            f"Student/user already exists: matric_no={matric_no}, email={email}, username={username}"
        )

    department_id = get_department_id(cursor, department_code)
    programme_id = get_programme_id(cursor, programme_code)
    password_hash = hash_password(plain_password)

    # 1. Create user account
    cursor.execute(
        """
        INSERT INTO users (role_id, username, email, password_hash)
        VALUES (%s, %s, %s, %s)
        RETURNING user_id
        """,
        (student_role_id, username, email, password_hash),
    )
    user_id = cursor.fetchone()[0]

    # 2. Create student profile
    cursor.execute(
        """
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
        """,
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
    student_id = cursor.fetchone()[0]

    # 3. Assign student to courses
    course_code_list = [code.strip() for code in course_codes.split(",") if code.strip()]

    if not course_code_list:
        raise ValueError(f"No course codes supplied for student {matric_no}")

    for course_code in course_code_list:
        course_id = get_course_id(cursor, course_code)

        cursor.execute(
            """
            INSERT INTO course_enrollments (
                student_id,
                course_id,
                academic_session,
                semester
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (student_id, course_id, academic_session, semester)
            DO NOTHING
            """,
            (student_id, course_id, "2025/2026", "Second"),
        )

    return matric_no


def upload_students():
    """Main function to upload students from CSV into PostgreSQL."""

    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found: {CSV_PATH}")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    validate_csv(df)

    successful_uploads = []
    failed_uploads = []

    connection = get_connection()

    try:
        cursor = connection.cursor()
        student_role_id = get_role_id(cursor, "Student")

        for index, row in df.iterrows():
            try:
                matric_no = create_student_from_row(cursor, row, student_role_id)
                connection.commit()
                successful_uploads.append(matric_no)
                print(f"SUCCESS: Uploaded student {matric_no}")

            except Exception as row_error:
                connection.rollback()
                failed_uploads.append((index + 2, str(row_error)))
                print(f"FAILED: Row {index + 2} - {row_error}")

        cursor.close()

    finally:
        connection.close()

    print("\n==============================")
    print("UPLOAD SUMMARY")
    print("==============================")
    print(f"Successful uploads: {len(successful_uploads)}")
    print(f"Failed uploads: {len(failed_uploads)}")

    if successful_uploads:
        print("\nUploaded matric numbers:")
        for matric_no in successful_uploads:
            print(f"- {matric_no}")

    if failed_uploads:
        print("\nFailed rows:")
        for row_number, error in failed_uploads:
            print(f"- Row {row_number}: {error}")


if __name__ == "__main__":
    upload_students()
