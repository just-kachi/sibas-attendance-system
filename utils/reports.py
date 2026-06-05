from utils.db import fetch_one, fetch_all


def get_attendance_threshold():
    """
    Gets attendance threshold from system settings.
    Default is 80 if not found.
    """
    query = """
        SELECT setting_value
        FROM system_settings
        WHERE setting_name = 'attendance_threshold'
    """

    result = fetch_one(query)

    if result is None:
        return 80

    return float(result["setting_value"])


def get_student_attendance_summary(student_id: int):
    """
    Gets attendance summary for a student across enrolled courses.
    """
    query = """
        SELECT
            c.course_code,
            c.course_title,
            COUNT(ats.session_id) AS total_sessions,
            COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN ar.status = 'Absent' THEN 1 END) AS absent_count,
            CASE
                WHEN COUNT(ats.session_id) = 0 THEN 0
                ELSE ROUND(
                    (COUNT(CASE WHEN ar.status = 'Present' THEN 1 END)::numeric
                    / COUNT(ats.session_id)::numeric) * 100,
                    2
                )
            END AS attendance_percentage
        FROM course_enrollments ce
        JOIN courses c ON ce.course_id = c.course_id
        LEFT JOIN attendance_sessions ats
            ON ats.course_id = c.course_id
            AND ats.academic_session = ce.academic_session
            AND ats.semester = ce.semester
        LEFT JOIN attendance_records ar
            ON ar.session_id = ats.session_id
            AND ar.student_id = ce.student_id
        WHERE ce.student_id = %s
          AND ce.is_active = TRUE
        GROUP BY c.course_code, c.course_title
        ORDER BY c.course_code
    """

    return fetch_all(query, (student_id,))


def get_courses_above_threshold(student_id: int):
    """
    Counts how many courses are above the attendance threshold.
    """
    threshold = get_attendance_threshold()
    summaries = get_student_attendance_summary(student_id)

    total_courses = len(summaries)
    above_threshold = 0

    for row in summaries:
        if float(row["attendance_percentage"]) >= threshold:
            above_threshold += 1

    return above_threshold, total_courses


def get_lecturer_courses(lecturer_id: int):
    """
    Gets courses assigned to a lecturer.
    """
    query = """
        SELECT
            c.course_id,
            c.course_code,
            c.course_title,
            lc.academic_session,
            lc.semester
        FROM lecturer_courses lc
        JOIN courses c ON lc.course_id = c.course_id
        WHERE lc.lecturer_id = %s
        ORDER BY c.course_code
    """

    return fetch_all(query, (lecturer_id,))


def get_course_attendance_report(course_code: str):
    """
    Gets attendance report for all enrolled students in a course.
    """
    query = """
        SELECT
            s.matric_no,
            s.first_name,
            s.last_name,
            c.course_code,
            c.course_title,
            COUNT(ats.session_id) AS total_sessions,
            COUNT(CASE WHEN ar.status = 'Present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN ar.status = 'Absent' THEN 1 END) AS absent_count,
            CASE
                WHEN COUNT(ats.session_id) = 0 THEN 0
                ELSE ROUND(
                    (COUNT(CASE WHEN ar.status = 'Present' THEN 1 END)::numeric
                    / COUNT(ats.session_id)::numeric) * 100,
                    2
                )
            END AS attendance_percentage
        FROM course_enrollments ce
        JOIN students s ON ce.student_id = s.student_id
        JOIN courses c ON ce.course_id = c.course_id
        LEFT JOIN attendance_sessions ats
            ON ats.course_id = c.course_id
            AND ats.academic_session = ce.academic_session
            AND ats.semester = ce.semester
        LEFT JOIN attendance_records ar
            ON ar.session_id = ats.session_id
            AND ar.student_id = s.student_id
        WHERE c.course_code = %s
          AND ce.is_active = TRUE
        GROUP BY
            s.matric_no,
            s.first_name,
            s.last_name,
            c.course_code,
            c.course_title
        ORDER BY s.matric_no
    """

    return fetch_all(query, (course_code,))


def get_department_summary():
    """
    Gets a simple department-level student count summary.
    """
    query = """
        SELECT
            d.department_name,
            COUNT(s.student_id) AS student_count
        FROM departments d
        LEFT JOIN students s ON d.department_id = s.department_id
        GROUP BY d.department_name
        ORDER BY d.department_name
    """

    return fetch_all(query)


def get_all_students():
    """
    Gets all registered students.
    """
    query = """
        SELECT
            s.student_id,
            u.username,
            s.matric_no,
            s.first_name,
            s.middle_name,
            s.last_name,
            s.email,
            s.level,
            d.department_name,
            p.programme_name
        FROM students s
        JOIN users u ON s.user_id = u.user_id
        JOIN departments d ON s.department_id = d.department_id
        JOIN programmes p ON s.programme_id = p.programme_id
        ORDER BY s.matric_no
    """

    return fetch_all(query)


def get_all_courses():
    """
    Gets all courses.
    """
    query = """
        SELECT
            c.course_id,
            c.course_code,
            c.course_title,
            c.credit_units,
            c.level,
            d.department_name
        FROM courses c
        JOIN departments d ON c.department_id = d.department_id
        ORDER BY c.course_code
    """

    return fetch_all(query)