from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

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


def generate_pdf_report(title: str, subtitle: str, columns: list, rows: list) -> bytes:
    """
    Generates a styled PDF report as bytes.

    Args:
        title:    Main heading e.g. 'Course Attendance Report'
        subtitle: Sub-heading e.g. 'DTS304 - Data Management I'
        columns:  List of column header strings
        rows:     List of lists — each inner list is one data row

    Returns:
        PDF file as bytes (ready for st.download_button)
    """

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#003366"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4,
        alignment=TA_CENTER,
    )

    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        spaceAfter=16,
        alignment=TA_CENTER,
    )

    generated_on = datetime.now().strftime("%d %B %Y, %I:%M %p")

    elements = [
        Paragraph("SIBAS — Attendance Report", title_style),
        Paragraph(title, subtitle_style),
        Paragraph(subtitle, subtitle_style),
        Paragraph(f"Generated: {generated_on}", meta_style),
    ]

    # Build table: header row + data rows
    table_data = [columns]
    for row in rows:
        table_data.append([str(cell) if cell is not None else "" for cell in row])

    # Spread columns evenly across the page width
    page_width = A4[0] - 4 * cm
    col_width = page_width / len(columns)
    col_widths = [col_width] * len(columns)

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([
        # Header row styling
        ("BACKGROUND",      (0, 0), (-1, 0),  colors.HexColor("#003366")),
        ("TEXTCOLOR",       (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",        (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",        (0, 0), (-1, 0),  9),
        ("BOTTOMPADDING",   (0, 0), (-1, 0),  8),
        ("TOPPADDING",      (0, 0), (-1, 0),  8),
        # Data rows styling
        ("FONTNAME",        (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",        (0, 1), (-1, -1), 8),
        ("TOPPADDING",      (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING",   (0, 1), (-1, -1), 5),
        # Alternating row colours
        ("ROWBACKGROUNDS",  (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        # Grid lines
        ("GRID",            (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("ALIGN",           (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",          (0, 0), (-1, -1), "MIDDLE"),
        ("WORDWRAP",        (0, 0), (-1, -1), True),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    total_style = ParagraphStyle(
        "Total",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#333333"),
    )
    elements.append(Paragraph(f"Total records: {len(rows)}", total_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
