import pandas as pd

from utils.db import get_connection


REQUIRED_COLUMNS = ["matric_no", "status"]
VALID_STATUSES = ["Present", "Absent"]


def validate_attendance_csv(df: pd.DataFrame):
    """
    Validates attendance CSV format and status values.
    """
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    if df.empty:
        raise ValueError("CSV file is empty.")

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


def get_lecturer_by_user_id(cursor, user_id: int):
    cursor.execute(
        """
        SELECT lecturer_id
        FROM lecturers
        WHERE user_id = %s
        """,
        (user_id,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError("Lecturer profile does not exist for this user.")

    return result[0]


def confirm_lecturer_teaches_course(
    cursor,
    lecturer_id: int,
    course_id: int,
    academic_session: str,
    semester: str,
):
    cursor.execute(
        """
        SELECT 1
        FROM lecturer_courses
        WHERE lecturer_id = %s
          AND course_id = %s
          AND academic_session = %s
          AND semester = %s
        """,
        (lecturer_id, course_id, academic_session, semester),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError("This lecturer is not assigned to this course.")


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


def confirm_student_enrolled(
    cursor,
    student_id: int,
    course_id: int,
    matric_no: str,
    academic_session: str,
    semester: str,
):
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
        (student_id, course_id, academic_session, semester),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Student '{matric_no}' is not enrolled in this course.")


def create_attendance_session(
    cursor,
    course_id: int,
    lecturer_id: int,
    session_date: str,
    topic: str,
    academic_session: str,
    semester: str,
):
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
            session_date,
            topic,
            academic_session,
            semester,
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


def upload_attendance_from_dataframe(
    df: pd.DataFrame,
    course_code: str,
    lecturer_user_id: int,
    session_date: str,
    topic: str,
    academic_session: str = "2025/2026",
    semester: str = "Second",
):
    """
    Uploads attendance records from a DataFrame.
    This is useful for Streamlit lecturer attendance upload.
    """
    validate_attendance_csv(df)

    successful_records = []
    failed_records = []

    connection = get_connection()

    try:
        cursor = connection.cursor()

        course_id = get_course_id(cursor, course_code)
        lecturer_id = get_lecturer_by_user_id(cursor, lecturer_user_id)

        confirm_lecturer_teaches_course(
            cursor,
            lecturer_id,
            course_id,
            academic_session,
            semester,
        )

        session_id = create_attendance_session(
            cursor,
            course_id,
            lecturer_id,
            session_date,
            topic,
            academic_session,
            semester,
        )

        for index, row in df.iterrows():
            try:
                matric_no = str(row["matric_no"]).strip()
                status = str(row["status"]).strip()

                student_id = get_student_by_matric_no(cursor, matric_no)

                confirm_student_enrolled(
                    cursor,
                    student_id,
                    course_id,
                    matric_no,
                    academic_session,
                    semester,
                )

                insert_attendance_record(
                    cursor,
                    session_id,
                    student_id,
                    status,
                    lecturer_user_id,
                )

                successful_records.append((matric_no, status))

            except Exception as row_error:
                failed_records.append((index + 2, str(row_error)))

        if failed_records:
            connection.rollback()
        else:
            connection.commit()

        cursor.close()

    finally:
        connection.close()

    return session_id, successful_records, failed_records

def get_lecturer_sessions(lecturer_user_id: int):
    """
    Gets all attendance sessions owned by a lecturer.
    """
    connection = get_connection()

    try:
        cursor = connection.cursor()

        lecturer_id = get_lecturer_by_user_id(cursor, lecturer_user_id)

        cursor.execute(
            """
            SELECT
                ats.session_id,
                c.course_code,
                c.course_title,
                ats.session_date,
                ats.topic,
                ats.academic_session,
                ats.semester
            FROM attendance_sessions ats
            JOIN courses c ON ats.course_id = c.course_id
            WHERE ats.lecturer_id = %s
            ORDER BY ats.session_date DESC, ats.session_id DESC
            """,
            (lecturer_id,),
        )

        rows = cursor.fetchall()
        cursor.close()

        sessions = []

        for row in rows:
            sessions.append(
                {
                    "session_id": row[0],
                    "course_code": row[1],
                    "course_title": row[2],
                    "session_date": row[3],
                    "topic": row[4],
                    "academic_session": row[5],
                    "semester": row[6],
                }
            )

        return sessions

    finally:
        connection.close()


def get_attendance_records_for_session(session_id: int, lecturer_user_id: int):
    """
    Gets attendance records for a session owned by the lecturer.
    """
    connection = get_connection()

    try:
        cursor = connection.cursor()

        lecturer_id = get_lecturer_by_user_id(cursor, lecturer_user_id)

        cursor.execute(
            """
            SELECT 1
            FROM attendance_sessions
            WHERE session_id = %s
              AND lecturer_id = %s
            """,
            (session_id, lecturer_id),
        )

        owns_session = cursor.fetchone()

        if owns_session is None:
            raise ValueError("You do not own this attendance session.")

        cursor.execute(
            """
            SELECT
                ar.record_id,
                s.matric_no,
                s.first_name,
                s.last_name,
                ar.status,
                ar.updated_at
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.student_id
            WHERE ar.session_id = %s
            ORDER BY s.matric_no
            """,
            (session_id,),
        )

        rows = cursor.fetchall()
        cursor.close()

        records = []

        for row in rows:
            records.append(
                {
                    "record_id": row[0],
                    "matric_no": row[1],
                    "first_name": row[2],
                    "last_name": row[3],
                    "status": row[4],
                    "updated_at": row[5],
                }
            )

        return records

    finally:
        connection.close()


def update_attendance_record(record_id: int, new_status: str, lecturer_user_id: int):
    """
    Allows a lecturer to manually correct/override an attendance record.
    The lecturer must own the attendance session connected to the record.
    """

    if new_status not in VALID_STATUSES:
        raise ValueError("Status must be either Present or Absent.")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        lecturer_id = get_lecturer_by_user_id(cursor, lecturer_user_id)

        cursor.execute(
            """
            SELECT ar.record_id
            FROM attendance_records ar
            JOIN attendance_sessions ats ON ar.session_id = ats.session_id
            WHERE ar.record_id = %s
              AND ats.lecturer_id = %s
            """,
            (record_id, lecturer_id),
        )

        record = cursor.fetchone()

        if record is None:
            raise ValueError("You cannot update this attendance record.")

        cursor.execute(
            """
            UPDATE attendance_records
            SET status = %s,
                uploaded_by = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE record_id = %s
            """,
            (new_status, lecturer_user_id, record_id),
        )

        connection.commit()
        cursor.close()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()