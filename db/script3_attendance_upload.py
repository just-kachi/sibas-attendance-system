import os
import sys
import pandas as pd
import psycopg2


# ============================================================
# DATABASE CONNECTION SETTINGS
# ============================================================

DB_NAME = "sibas_db"
DB_USER = "postgres"
DB_PASSWORD = "kachi123"
DB_HOST = "localhost"
DB_PORT = "5432"


# ============================================================
# ATTENDANCE UPLOAD SETTINGS
# You can change these when testing another course/session.
# ============================================================

COURSE_CODE = "DTS304"
LECTURER_USERNAME = "lecturer1"
SESSION_DATE = "2026-06-05"
TOPIC = "Week 1 Attendance"
ACADEMIC_SESSION = "2025/2026"
SEMESTER = "Second"


# ============================================================
# FILE PATH
# This points to uploads/sample_attendance.csv
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "uploads", "sample_attendance.csv")


REQUIRED_COLUMNS = ["matric_no", "status"]
VALID_STATUSES = ["Present", "Absent"]


def get_connection():
    """Create and return a PostgreSQL database connection."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def validate_csv(df: pd.DataFrame):
    """Validate required columns and attendance status values."""
    missing_columns = []

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    for index, row in df.iterrows():
        status = str(row["status"]).strip()

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}' on row {index + 2}. "
                "Status must be either 'Present' or 'Absent'."
            )


def get_course_id(cursor, course_code: str):
    cursor.execute(
        "SELECT course_id FROM courses WHERE course_code = %s",
        (course_code,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Course code '{course_code}' does not exist.")

    return result[0]


def get_lecturer_by_username(cursor, username: str):
    cursor.execute(
        """
        SELECT l.lecturer_id, u.user_id
        FROM lecturers l
        JOIN users u ON l.user_id = u.user_id
        WHERE u.username = %s
        """,
        (username,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Lecturer username '{username}' does not exist.")

    lecturer_id, user_id = result
    return lecturer_id, user_id


def confirm_lecturer_teaches_course(cursor, lecturer_id: int, course_id: int):
    cursor.execute(
        """
        SELECT 1
        FROM lecturer_courses
        WHERE lecturer_id = %s
          AND course_id = %s
          AND academic_session = %s
          AND semester = %s
        """,
        (lecturer_id, course_id, ACADEMIC_SESSION, SEMESTER),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "This lecturer is not assigned to this course for the selected session/semester."
        )


def get_student_by_matric_no(cursor, matric_no: str):
    cursor.execute(
        """
        SELECT student_id
        FROM students
        WHERE matric_no = %s
        """,
        (matric_no,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Student with matric_no '{matric_no}' does not exist.")

    return result[0]


def confirm_student_enrolled(cursor, student_id: int, course_id: int, matric_no: str):
    cursor.execute(
        """
        SELECT 1
        FROM course_enrollments
        WHERE student_id = %s
          AND course_id = %s
          AND academic_session = %s
          AND semester = %s
          AND is_active = TRUE
        """,
        (student_id, course_id, ACADEMIC_SESSION, SEMESTER),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(
            f"Student '{matric_no}' is not enrolled in this course for "
            f"{ACADEMIC_SESSION} {SEMESTER} semester."
        )


def create_attendance_session(cursor, course_id: int, lecturer_id: int):
    """
    Create an attendance session.

    This allows multiple sessions for the same course on different dates/topics.
    If you run the script multiple times with the same values, it will create
    another session unless you add duplicate-check logic.
    """
    cursor.execute(
        """
        INSERT INTO attendance_sessions (
            course_id,
            lecturer_id,
            session_date,
            topic,
            academic_session,
            semester
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING session_id
        """,
        (
            course_id,
            lecturer_id,
            SESSION_DATE,
            TOPIC,
            ACADEMIC_SESSION,
            SEMESTER,
        ),
    )

    return cursor.fetchone()[0]


def insert_attendance_record(
    cursor,
    session_id: int,
    student_id: int,
    status: str,
    uploaded_by: int,
):
    cursor.execute(
        """
        INSERT INTO attendance_records (
            session_id,
            student_id,
            status,
            uploaded_by
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (session_id, student_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            uploaded_by = EXCLUDED.uploaded_by,
            updated_at = CURRENT_TIMESTAMP
        """,
        (session_id, student_id, status, uploaded_by),
    )


def upload_attendance():
    """Main function to upload attendance records from CSV."""

    if not os.path.exists(CSV_PATH):
        print(f"CSV file not found: {CSV_PATH}")
        sys.exit(1)

    df = pd.read_csv(CSV_PATH)
    validate_csv(df)

    successful_records = []
    failed_records = []

    connection = get_connection()

    try:
        cursor = connection.cursor()

        course_id = get_course_id(cursor, COURSE_CODE)
        lecturer_id, lecturer_user_id = get_lecturer_by_username(cursor, LECTURER_USERNAME)

        confirm_lecturer_teaches_course(cursor, lecturer_id, course_id)

        session_id = create_attendance_session(cursor, course_id, lecturer_id)

        print("Attendance session created successfully.")
        print(f"Session ID: {session_id}")
        print(f"Course: {COURSE_CODE}")
        print(f"Lecturer: {LECTURER_USERNAME}")
        print(f"Date: {SESSION_DATE}")
        print()

        for index, row in df.iterrows():
            try:
                matric_no = str(row["matric_no"]).strip()
                status = str(row["status"]).strip()

                student_id = get_student_by_matric_no(cursor, matric_no)
                confirm_student_enrolled(cursor, student_id, course_id, matric_no)

                insert_attendance_record(
                    cursor=cursor,
                    session_id=session_id,
                    student_id=student_id,
                    status=status,
                    uploaded_by=lecturer_user_id,
                )

                successful_records.append((matric_no, status))
                print(f"SUCCESS: {matric_no} marked as {status}")

            except Exception as row_error:
                failed_records.append((index + 2, str(row_error)))
                print(f"FAILED: Row {index + 2} - {row_error}")

        if failed_records:
            connection.rollback()
            print("\nUpload rolled back because some rows failed.")
            print("Fix the failed rows and run the script again.")
        else:
            connection.commit()
            print("\nAttendance upload committed successfully.")

        cursor.close()

    except Exception as error:
        connection.rollback()
        print(f"Error: {error}")

    finally:
        connection.close()

    print("\n==============================")
    print("ATTENDANCE UPLOAD SUMMARY")
    print("==============================")
    print(f"Successful records: {len(successful_records)}")
    print(f"Failed records: {len(failed_records)}")

    if successful_records:
        print("\nUploaded attendance records:")
        for matric_no, status in successful_records:
            print(f"- {matric_no}: {status}")

    if failed_records:
        print("\nFailed rows:")
        for row_number, error in failed_records:
            print(f"- Row {row_number}: {error}")


if __name__ == "__main__":
    upload_attendance()
