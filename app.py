import pandas as pd
import streamlit as st

from utils.auth import (
    authenticate_user,
    get_student_profile,
    get_lecturer_profile,
    get_admin_profile,
)
from utils.student_upload import upload_students_from_dataframe
from utils.attendance_upload import (
    upload_attendance_from_dataframe,
    get_lecturer_sessions,
    get_attendance_records_for_session,
    update_attendance_record,
)
from utils.reports import (
    get_attendance_threshold,
    get_student_attendance_summary,
    get_courses_above_threshold,
    get_lecturer_courses,
    get_course_attendance_report,
    get_department_summary,
    get_all_students,
    get_all_courses,
    generate_pdf_report,
)
from utils.admin import (
    get_departments,
    get_programmes,
    get_courses_for_admin,
    create_student,
    create_department,
    create_programme,
    create_course,
    create_lecturer,
    get_lecturer_users,
    assign_lecturer_to_course,
    get_all_lecturers,
    get_lecturer_course_assignments,
    update_lecturer,
    update_student,
    get_student_course_ids,
    update_student_course_enrollments,
    set_user_active_status,
    delete_user,
    get_all_students_with_status,
    get_all_lecturers_with_status,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SIBAS Attendance System",
    page_icon="📘",
    layout="wide",
)


# ============================================================
# BASIC STYLING
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            color: #003366;
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 5px;
        }

        .sub-title {
            color: #333333;
            font-size: 18px;
            margin-bottom: 25px;
        }

        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e6e6e6;
            box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }

        .course-title {
            color: #003366;
            font-size: 20px;
            font-weight: 700;
        }

        .small-text {
            color: #666666;
            font-size: 14px;
        }

        .success-text {
            color: green;
            font-weight: 700;
        }

        .danger-text {
            color: red;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Home"


# ============================================================
# HELPERS
# ============================================================

def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.selected_page = "Home"
    st.rerun()


def dataframe_to_csv_download(df: pd.DataFrame):
    return df.to_csv(index=False).encode("utf-8")


def show_home_page():
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown('<div class="main-title">SIBAS</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sub-title">Student Information Biometrics Attendance System</div>',
            unsafe_allow_html=True,
        )

        st.write(
            """
            Monitor student attendance with ease. This redesigned SIBAS platform
            supports administrators, lecturers, and students using a PostgreSQL-backed
            attendance management system.
            """
        )

        st.info(
            "Use the Login page to access the system as an Administrator, Lecturer, or Student."
        )

    with col2:
        st.markdown("### Core Features")
        st.write("- Role-based login")
        st.write("- Student registration and CSV upload")
        st.write("- Course enrollment")
        st.write("- Lecturer attendance sessions")
        st.write("- Attendance CSV upload")
        st.write("- Student attendance dashboard")
        st.write("- Reports and CSV export")


def show_login_page():
    st.markdown('<div class="main-title">Login</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        username_or_email = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = authenticate_user(username_or_email, password)

        if user is None:
            st.error("Invalid login details or inactive account.")
        else:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success("Login successful.")
            st.rerun()


def show_help_page():
    st.markdown('<div class="main-title">Help & Support</div>', unsafe_allow_html=True)

    st.markdown("### What is SIBAS?")
    st.write(
        """
        SIBAS is a Student Information Biometrics Attendance System. In this project,
        the system is redesigned as a PostgreSQL and Streamlit-based attendance platform.
        """
    )

    st.markdown("### Student CSV Format")
    st.code(
        """username,email,password,matric_no,first_name,middle_name,last_name,department_code,programme_code,level,course_codes
john231,john231@pau.edu.ng,password123,2310001,John,Ade,Okafor,CSC,BSC-CS,300,"DTS304,CSC313"
""",
        language="csv",
    )

    st.markdown("### Attendance CSV Format")
    st.code(
        """matric_no,status
23120111011,Present
23120111012,Absent
""",
        language="csv",
    )

    st.warning("Attendance status must be either Present or Absent.")


# ============================================================
# STUDENT PAGES
# ============================================================

def show_student_dashboard():
    user = st.session_state.user
    profile = get_student_profile(user["user_id"])

    if profile is None:
        st.error("Student profile not found.")
        return

    full_name = f"{profile['first_name']} {profile['last_name']}"
    st.markdown(f'<div class="main-title">Hello, {full_name}</div>', unsafe_allow_html=True)

    threshold = get_attendance_threshold()
    above_threshold, total_courses = get_courses_above_threshold(profile["student_id"])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Courses Above Threshold", f"{above_threshold} / {total_courses}")

    with col2:
        st.metric("Attendance Threshold", f"{threshold}%")

    with col3:
        st.metric("Level", profile["level"])

    st.markdown("## All Courses")

    summaries = get_student_attendance_summary(profile["student_id"])

    if not summaries:
        st.info("No course enrollment found.")
        return

    for row in summaries:
        percentage = float(row["attendance_percentage"])
        status = "Eligible" if percentage >= threshold else "Ineligible"

        with st.container():
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)

            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])

            with col_a:
                st.markdown(
                    f"<div class='course-title'>{row['course_code']} - {row['course_title']}</div>",
                    unsafe_allow_html=True,
                )
                if status == "Eligible":
                    st.markdown(
                        f"<div class='success-text'>{status}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div class='danger-text'>{status}</div>",
                        unsafe_allow_html=True,
                    )

            with col_b:
                st.metric("Attendance", f"{percentage}%")

            with col_c:
                st.metric("Present", row["present_count"])

            with col_d:
                st.metric("Absent", row["absent_count"])

            st.write(f"Total sessions: {row['total_sessions']}")
            st.markdown("</div>", unsafe_allow_html=True)


def show_student_profile():
    user = st.session_state.user
    profile = get_student_profile(user["user_id"])

    if profile is None:
        st.error("Student profile not found.")
        return

    st.markdown('<div class="main-title">My Profile</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("First Name", profile["first_name"], disabled=True)
        st.text_input("Middle Name", profile["middle_name"] or "", disabled=True)
        st.text_input("Last Name", profile["last_name"], disabled=True)
        st.text_input("Matric No.", profile["matric_no"], disabled=True)

    with col2:
        st.text_input("Email", profile["email"], disabled=True)
        st.text_input("Department", profile["department_name"], disabled=True)
        st.text_input("Programme", profile["programme_name"], disabled=True)
        st.text_input("Level", str(profile["level"]), disabled=True)


# ============================================================
# LECTURER PAGES
# ============================================================

def show_lecturer_dashboard():
    user = st.session_state.user
    profile = get_lecturer_profile(user["user_id"])

    if profile is None:
        st.error("Lecturer profile not found.")
        return

    st.markdown(
        f'<div class="main-title">Welcome, {profile["first_name"]} {profile["last_name"]}</div>',
        unsafe_allow_html=True,
    )

    st.write(f"Department: **{profile['department_name']}**")
    st.write(f"Staff No: **{profile['staff_no']}**")

    courses = get_lecturer_courses(profile["lecturer_id"])

    st.markdown("## My Courses")

    if not courses:
        st.info("No courses assigned yet.")
        return

    df = pd.DataFrame(courses)
    st.dataframe(df, use_container_width=True)


def show_attendance_upload_page():
    user = st.session_state.user
    profile = get_lecturer_profile(user["user_id"])

    if profile is None:
        st.error("Lecturer profile not found.")
        return

    st.markdown('<div class="main-title">Upload Attendance</div>', unsafe_allow_html=True)

    lecturer_courses = get_lecturer_courses(profile["lecturer_id"])

    if not lecturer_courses:
        st.warning("You have no assigned courses.")
        return

    course_options = [
        f"{course['course_code']} - {course['course_title']}"
        for course in lecturer_courses
    ]

    selected_course = st.selectbox("Select Course", course_options)
    selected_course_code = selected_course.split(" - ")[0]

    session_date = st.date_input("Session Date")
    topic = st.text_input("Topic", value="Class Attendance")
    academic_session = st.text_input("Academic Session", value="2025/2026")
    semester = st.selectbox("Semester", ["First", "Second"], index=1)

    uploaded_file = st.file_uploader(
        "Upload attendance CSV",
        type=["csv"],
        help="CSV must contain matric_no and status columns.",
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True)

        if st.button("Submit Attendance"):
            try:
                session_id, successful, failed = upload_attendance_from_dataframe(
                    df=df,
                    course_code=selected_course_code,
                    lecturer_user_id=user["user_id"],
                    session_date=str(session_date),
                    topic=topic,
                    academic_session=academic_session,
                    semester=semester,
                )

                if failed:
                    st.error("Attendance upload failed. No records were saved.")
                    st.write("Failed rows:")
                    st.write(failed)
                else:
                    st.success(f"Attendance uploaded successfully. Session ID: {session_id}")
                    st.write(f"Successful records: {len(successful)}")
                    st.dataframe(
                        pd.DataFrame(successful, columns=["matric_no", "status"]),
                        use_container_width=True,
                    )

            except Exception as error:
                st.error(f"Error: {error}")


def show_correct_attendance_page():
    user = st.session_state.user

    st.markdown('<div class="main-title">Correct Attendance</div>', unsafe_allow_html=True)

    sessions = get_lecturer_sessions(user["user_id"])

    if not sessions:
        st.info("No attendance sessions found.")
        return

    session_options = [
        f"{session['session_id']} - {session['course_code']} - {session['session_date']} - {session['topic']}"
        for session in sessions
    ]

    selected_session = st.selectbox("Select Attendance Session", session_options)
    selected_session_id = int(selected_session.split(" - ")[0])

    records = get_attendance_records_for_session(
        session_id=selected_session_id,
        lecturer_user_id=user["user_id"],
    )

    if not records:
        st.info("No attendance records found for this session.")
        return

    st.markdown("### Attendance Records")
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True)

    st.markdown("### Correct a Record")

    record_options = [
        f"{record['record_id']} - {record['matric_no']} - {record['first_name']} {record['last_name']} - {record['status']}"
        for record in records
    ]

    selected_record = st.selectbox("Select Student Record", record_options)
    selected_record_id = int(selected_record.split(" - ")[0])

    new_status = st.selectbox("New Status", ["Present", "Absent"])

    if st.button("Update Attendance Record"):
        try:
            update_attendance_record(
                record_id=selected_record_id,
                new_status=new_status,
                lecturer_user_id=user["user_id"],
            )

            st.success("Attendance record updated successfully.")
            st.rerun()

        except Exception as error:
            st.error(f"Error: {error}")


def show_lecturer_course_report():
    user = st.session_state.user
    profile = get_lecturer_profile(user["user_id"])

    if profile is None:
        st.error("Lecturer profile not found.")
        return

    st.markdown('<div class="main-title">Course Attendance Report</div>', unsafe_allow_html=True)

    courses = get_lecturer_courses(profile["lecturer_id"])

    if not courses:
        st.info("No courses assigned.")
        return

    course_options = [
        f"{course['course_code']} - {course['course_title']}"
        for course in courses
    ]

    selected_course = st.selectbox("Select Course", course_options)
    selected_course_code = selected_course.split(" - ")[0]

    report = get_course_attendance_report(selected_course_code)

    if not report:
        st.info("No report data found.")
        return

    df = pd.DataFrame(report)
    st.dataframe(df, use_container_width=True)

    csv_data = dataframe_to_csv_download(df)
    st.download_button(
        "Download CSV Report",
        data=csv_data,
        file_name=f"{selected_course_code}_attendance_report.csv",
        mime="text/csv",
    )


# ============================================================
# ADMIN PAGES
# ============================================================

def show_admin_create_lecturer():
    st.markdown('<div class="main-title">Create Lecturer</div>', unsafe_allow_html=True)

    departments = get_departments()

    if not departments:
        st.error("No departments found. Create a department first.")
        return

    department_options = [
        f"{dept['department_id']} - {dept['department_name']} ({dept['department_code']})"
        for dept in departments
    ]

    st.markdown("### Lecturer Login Details")

    with st.form("create_lecturer_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Temporary Password", type="password")

        st.markdown("### Lecturer Profile")

        staff_no = st.text_input("Staff Number")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        phone_number = st.text_input("Phone Number")

        selected_department = st.selectbox("Department", department_options)
        department_id = int(selected_department.split(" - ")[0])

        submitted = st.form_submit_button("Create Lecturer")

    if submitted:
        try:
            if not username or not email or not password or not staff_no or not first_name or not last_name:
                st.error("Please fill all required fields.")
            else:
                user_id = create_lecturer(
                    username=username,
                    email=email,
                    password=password,
                    staff_no=staff_no,
                    first_name=first_name,
                    last_name=last_name,
                    phone_number=phone_number,
                    department_id=department_id,
                )

                st.success(f"Lecturer created successfully. User ID: {user_id}")
                st.info("The lecturer can now log in with the username and temporary password.")

        except Exception as error:
            st.error(f"Error: {error}")

def show_admin_manage_academics():
    st.markdown('<div class="main-title">Manage Academics</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Create Department", "Create Programme", "Create Course"])

    with tab1:
        st.markdown("### Create Department")

        with st.form("create_department_form"):
            department_name = st.text_input("Department Name", placeholder="Computer Science")
            department_code = st.text_input("Department Code", placeholder="CSC")

            submitted = st.form_submit_button("Create Department")

        if submitted:
            try:
                if not department_name or not department_code:
                    st.error("Please fill all fields.")
                else:
                    create_department(
                        department_name=department_name,
                        department_code=department_code.upper(),
                    )
                    st.success("Department created successfully.")
            except Exception as error:
                st.error(f"Error: {error}")

    with tab2:
        st.markdown("### Create Programme")

        departments = get_departments()

        if not departments:
            st.warning("Create a department first.")
        else:
            department_options = [
                f"{dept['department_id']} - {dept['department_name']} ({dept['department_code']})"
                for dept in departments
            ]

            with st.form("create_programme_form"):
                selected_department = st.selectbox("Department", department_options)
                department_id = int(selected_department.split(" - ")[0])

                programme_name = st.text_input("Programme Name", placeholder="BSc Computer Science")
                programme_code = st.text_input("Programme Code", placeholder="BSC-CS")

                submitted = st.form_submit_button("Create Programme")

            if submitted:
                try:
                    if not programme_name or not programme_code:
                        st.error("Please fill all fields.")
                    else:
                        create_programme(
                            department_id=department_id,
                            programme_name=programme_name,
                            programme_code=programme_code.upper(),
                        )
                        st.success("Programme created successfully.")
                except Exception as error:
                    st.error(f"Error: {error}")

    with tab3:
        st.markdown("### Create Course")

        departments = get_departments()

        if not departments:
            st.warning("Create a department first.")
        else:
            department_options = [
                f"{dept['department_id']} - {dept['department_name']} ({dept['department_code']})"
                for dept in departments
            ]

            with st.form("create_course_form"):
                selected_department = st.selectbox("Department", department_options, key="course_dept")
                department_id = int(selected_department.split(" - ")[0])

                course_code = st.text_input("Course Code", placeholder="DTS304")
                course_title = st.text_input("Course Title", placeholder="Data Management I")
                credit_units = st.number_input("Credit Units", min_value=1, max_value=10, value=3)
                level = st.selectbox("Level", [100, 200, 300, 400, 500], index=2)

                submitted = st.form_submit_button("Create Course")

            if submitted:
                try:
                    if not course_code or not course_title:
                        st.error("Please fill all required fields.")
                    else:
                        create_course(
                            department_id=department_id,
                            course_code=course_code.upper(),
                            course_title=course_title,
                            credit_units=int(credit_units),
                            level=int(level),
                        )
                        st.success("Course created successfully.")
                except Exception as error:
                    st.error(f"Error: {error}")


def show_admin_create_student():
    st.markdown('<div class="main-title">Create Student</div>', unsafe_allow_html=True)

    departments = get_departments()
    programmes = get_programmes()
    courses = get_courses_for_admin()

    if not departments:
        st.error("No departments found.")
        return

    if not programmes:
        st.error("No programmes found.")
        return

    if not courses:
        st.error("No courses found.")
        return

    department_options = [
        f"{dept['department_id']} - {dept['department_name']} ({dept['department_code']})"
        for dept in departments
    ]

    programme_options = [
        f"{programme['programme_id']} - {programme['programme_name']} ({programme['programme_code']})"
        for programme in programmes
    ]

    course_options = {
        f"{course['course_id']} - {course['course_code']} - {course['course_title']}": course["course_id"]
        for course in courses
    }

    with st.form("create_student_form"):
        st.markdown("### Student Login Details")

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Temporary Password", type="password")

        st.markdown("### Student Profile")

        matric_no = st.text_input("Matric Number")
        first_name = st.text_input("First Name")
        middle_name = st.text_input("Middle Name")
        last_name = st.text_input("Last Name")

        selected_department = st.selectbox("Department", department_options)
        department_id = int(selected_department.split(" - ")[0])

        selected_programme = st.selectbox("Programme", programme_options)
        programme_id = int(selected_programme.split(" - ")[0])

        level = st.selectbox("Level", [100, 200, 300, 400, 500], index=2)

        selected_courses = st.multiselect(
            "Assign Courses",
            list(course_options.keys()),
        )

        academic_session = st.text_input("Academic Session", value="2025/2026")
        semester = st.selectbox("Semester", ["First", "Second"], index=1)

        submitted = st.form_submit_button("Create Student")

    if submitted:
        try:
            if not username or not email or not password or not matric_no or not first_name or not last_name:
                st.error("Please fill all required fields.")
                return

            course_ids = [course_options[item] for item in selected_courses]

            student_id = create_student(
                username=username,
                email=email,
                password=password,
                matric_no=matric_no,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                department_id=department_id,
                programme_id=programme_id,
                level=level,
                course_ids=course_ids,
                academic_session=academic_session,
                semester=semester,
            )

            st.success(f"Student created successfully. Student ID: {student_id}")

        except Exception as error:
            st.error(f"Error: {error}")


def show_admin_dashboard():
    user = st.session_state.user
    profile = get_admin_profile(user["user_id"])

    st.markdown('<div class="main-title">Admin Dashboard</div>', unsafe_allow_html=True)

    if profile:
        st.write(f"Welcome, **{profile['first_name']} {profile['last_name']}**")
    else:
        st.info("Admin profile has not been created yet, but your admin user login is active.")

    students = get_all_students()
    courses = get_all_courses()
    departments = get_department_summary()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Students", len(students))

    with col2:
        st.metric("Courses", len(courses))

    with col3:
        st.metric("Departments", len(departments))

    st.markdown("## Department Summary")
    st.dataframe(pd.DataFrame(departments), use_container_width=True)


def show_admin_student_upload():
    st.markdown('<div class="main-title">Bulk Student Upload</div>', unsafe_allow_html=True)

    st.write("Upload a CSV file containing student details and course assignments.")

    uploaded_file = st.file_uploader(
        "Upload student CSV",
        type=["csv"],
        help="CSV must match the required student registration format.",
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        st.markdown("### Preview")
        st.dataframe(df, use_container_width=True)

        if st.button("Upload Students"):
            try:
                successful, failed = upload_students_from_dataframe(df)

                st.success(f"Successful uploads: {len(successful)}")

                if successful:
                    st.write("Uploaded matric numbers:")
                    st.write(successful)

                if failed:
                    st.error(f"Failed uploads: {len(failed)}")
                    st.write(failed)

            except Exception as error:
                st.error(f"Error: {error}")


def show_admin_students():
    st.markdown('<div class="main-title">Registered Students</div>', unsafe_allow_html=True)

    students = get_all_students()

    if not students:
        st.info("No students found.")
        return

    st.markdown("## Student List")

    df = pd.DataFrame(students)
    st.dataframe(df, use_container_width=True)

    csv_data = dataframe_to_csv_download(df)
    st.download_button(
        "Download Students CSV",
        data=csv_data,
        file_name="students.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("## Edit Student")

    student_options = [
        f"{student['student_id']} - {student['matric_no']} - {student['first_name']} {student['last_name']}"
        for student in students
    ]

    selected_student = st.selectbox("Select Student to Edit", student_options)
    selected_student_id = int(selected_student.split(" - ")[0])

    student_data = None

    for student in students:
        if student["student_id"] == selected_student_id:
            student_data = student
            break

    if student_data is None:
        st.error("Selected student not found.")
        return

    departments = get_departments()
    programmes = get_programmes()
    courses = get_courses_for_admin()

    if not departments:
        st.error("No departments found.")
        return

    if not programmes:
        st.error("No programmes found.")
        return

    if not courses:
        st.error("No courses found.")
        return

    department_options = [
        f"{dept['department_id']} - {dept['department_name']} ({dept['department_code']})"
        for dept in departments
    ]

    programme_options = [
        f"{programme['programme_id']} - {programme['programme_name']} ({programme['programme_code']})"
        for programme in programmes
    ]

    course_options = {
        f"{course['course_id']} - {course['course_code']} - {course['course_title']}": course["course_id"]
        for course in courses
    }

    current_department_index = 0
    for index, dept in enumerate(departments):
        if dept["department_name"] == student_data["department_name"]:
            current_department_index = index
            break

    current_programme_index = 0
    for index, programme in enumerate(programmes):
        if programme["programme_name"] == student_data["programme_name"]:
            current_programme_index = index
            break

    academic_session = st.text_input(
        "Academic Session for Course Enrollments",
        value="2025/2026",
    )

    semester = st.selectbox(
        "Semester for Course Enrollments",
        ["First", "Second"],
        index=1,
    )

    current_course_ids = get_student_course_ids(
        selected_student_id,
        academic_session,
        semester,
    )

    default_selected_courses = [
        label
        for label, course_id in course_options.items()
        if course_id in current_course_ids
    ]

    with st.form("edit_student_form"):
        st.markdown("### Login Details")

        username = st.text_input("Username", value=student_data["username"])
        login_email = st.text_input("Login Email", value=student_data["email"])

        st.markdown("### Student Profile")

        matric_no = st.text_input("Matric Number", value=student_data["matric_no"])
        first_name = st.text_input("First Name", value=student_data["first_name"])
        middle_name = st.text_input("Middle Name", value=student_data["middle_name"] or "")
        last_name = st.text_input("Last Name", value=student_data["last_name"])
        student_email = st.text_input("Student Email", value=student_data["email"])

        selected_department = st.selectbox(
            "Department",
            department_options,
            index=current_department_index,
        )
        department_id = int(selected_department.split(" - ")[0])

        selected_programme = st.selectbox(
            "Programme",
            programme_options,
            index=current_programme_index,
        )
        programme_id = int(selected_programme.split(" - ")[0])

        level_values = [100, 200, 300, 400, 500]
        level = st.selectbox(
            "Level",
            level_values,
            index=level_values.index(int(student_data["level"])),
        )

        selected_courses = st.multiselect(
            "Assigned Courses",
            list(course_options.keys()),
            default=default_selected_courses,
        )

        submitted = st.form_submit_button("Update Student")

    if submitted:
        try:
            if not username or not login_email or not matric_no or not first_name or not last_name or not student_email:
                st.error("Please fill all required fields.")
                return

            selected_course_ids = [course_options[item] for item in selected_courses]

            update_student(
                student_id=selected_student_id,
                username=username,
                login_email=login_email,
                matric_no=matric_no,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                student_email=student_email,
                department_id=department_id,
                programme_id=programme_id,
                level=int(level),
            )

            update_student_course_enrollments(
                student_id=selected_student_id,
                course_ids=selected_course_ids,
                academic_session=academic_session,
                semester=semester,
            )

            st.success("Student updated successfully.")
            st.rerun()

        except Exception as error:
            st.error(f"Error: {error}")


def show_admin_lecturers():
    st.markdown('<div class="main-title">Lecturers</div>', unsafe_allow_html=True)

    lecturers = get_all_lecturers()

    if not lecturers:
        st.info("No lecturers found.")
        return

    st.markdown("## Registered Lecturers")

    lecturer_df = pd.DataFrame(lecturers)
    st.dataframe(lecturer_df, use_container_width=True)

    csv_data = dataframe_to_csv_download(lecturer_df)
    st.download_button(
        "Download Lecturers CSV",
        data=csv_data,
        file_name="lecturers.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.markdown("## Lecturer Course Assignments")

    assignments = get_lecturer_course_assignments()

    if assignments:
        st.dataframe(pd.DataFrame(assignments), use_container_width=True)
    else:
        st.info("No lecturer-course assignments found.")

        st.markdown("---")
    st.markdown("## Assign Lecturer to Course(s)")

    lecturer_users = get_lecturer_users()
    courses = get_courses_for_admin()

    if not lecturer_users:
        st.info("No lecturers found. Create a lecturer first.")
    elif not courses:
        st.info("No courses found. Create a course first.")
    else:
        lecturer_options_for_assignment = [
            f"{lecturer['user_id']} - {lecturer['first_name']} {lecturer['last_name']} ({lecturer['staff_no']})"
            for lecturer in lecturer_users
        ]

        course_options_for_assignment = {
            f"{course['course_id']} - {course['course_code']} - {course['course_title']}": course["course_id"]
            for course in courses
        }

        selected_lecturer_for_assignment = st.selectbox(
            "Select Lecturer",
            lecturer_options_for_assignment,
            key="assign_lecturer_select",
        )

        selected_courses_for_assignment = st.multiselect(
            "Select Course(s)",
            list(course_options_for_assignment.keys()),
            key="assign_courses_multiselect",
        )

        lecturer_user_id = int(selected_lecturer_for_assignment.split(" - ")[0])

        academic_session = st.text_input(
            "Academic Session",
            value="2025/2026",
            key="assign_academic_session",
        )

        semester = st.selectbox(
            "Semester",
            ["First", "Second"],
            index=1,
            key="assign_semester",
        )

        if st.button("Assign Lecturer to Selected Course(s)"):
            try:
                if not selected_courses_for_assignment:
                    st.error("Please select at least one course.")
                    return

                for selected_course in selected_courses_for_assignment:
                    course_id = course_options_for_assignment[selected_course]

                    assign_lecturer_to_course(
                        lecturer_user_id=lecturer_user_id,
                        course_id=course_id,
                        academic_session=academic_session,
                        semester=semester,
                    )

                st.success("Lecturer assigned to selected course(s) successfully.")
                st.rerun()

            except Exception as error:
                st.error(f"Error: {error}")

    st.markdown("---")
    st.markdown("## Edit Lecturer")

    lecturer_options = [
        f"{lecturer['lecturer_id']} - {lecturer['first_name']} {lecturer['last_name']} ({lecturer['staff_no']})"
        for lecturer in lecturers
    ]

    selected_lecturer = st.selectbox("Select Lecturer to Edit", lecturer_options)
    selected_lecturer_id = int(selected_lecturer.split(" - ")[0])

    lecturer_data = None

    for lecturer in lecturers:
        if lecturer["lecturer_id"] == selected_lecturer_id:
            lecturer_data = lecturer
            break

    if lecturer_data is None:
        st.error("Selected lecturer not found.")
        return

    departments = get_departments()

    if not departments:
        st.error("No departments found.")
        return

    department_options = [
        f"{dept['department_id']} - {dept['department_name']} ({dept['department_code']})"
        for dept in departments
    ]

    current_department_index = 0

    for index, dept in enumerate(departments):
        if dept["department_code"] == lecturer_data["department_code"]:
            current_department_index = index
            break

    with st.form("edit_lecturer_form"):
        username = st.text_input("Username", value=lecturer_data["username"])
        login_email = st.text_input("Login Email", value=lecturer_data["login_email"])

        staff_no = st.text_input("Staff Number", value=lecturer_data["staff_no"])
        first_name = st.text_input("First Name", value=lecturer_data["first_name"])
        last_name = st.text_input("Last Name", value=lecturer_data["last_name"])
        lecturer_email = st.text_input("Lecturer Email", value=lecturer_data["email"])
        phone_number = st.text_input("Phone Number", value=lecturer_data["phone_number"] or "")

        selected_department = st.selectbox(
            "Department",
            department_options,
            index=current_department_index,
        )
        department_id = int(selected_department.split(" - ")[0])

        submitted = st.form_submit_button("Update Lecturer")

    if submitted:
        try:
            if not username or not login_email or not staff_no or not first_name or not last_name or not lecturer_email:
                st.error("Please fill all required fields.")
                return

            update_lecturer(
                lecturer_id=selected_lecturer_id,
                username=username,
                login_email=login_email,
                staff_no=staff_no,
                first_name=first_name,
                last_name=last_name,
                lecturer_email=lecturer_email,
                phone_number=phone_number,
                department_id=department_id,
            )

            st.success("Lecturer updated successfully.")
            st.rerun()

        except Exception as error:
            st.error(f"Error: {error}")


def show_admin_courses():
    st.markdown('<div class="main-title">Courses</div>', unsafe_allow_html=True)

    courses = get_all_courses()

    if not courses:
        st.info("No courses found.")
        return

    df = pd.DataFrame(courses)
    st.dataframe(df, use_container_width=True)


def show_admin_reports():
    st.markdown('<div class="main-title">Reports</div>', unsafe_allow_html=True)

    courses = get_all_courses()

    if not courses:
        st.info("No courses found.")
        return

    course_options = [
        f"{course['course_code']} - {course['course_title']}"
        for course in courses
    ]

    selected_course = st.selectbox("Select Course", course_options)
    selected_course_code = selected_course.split(" - ")[0]

    report = get_course_attendance_report(selected_course_code)

    if not report:
        st.info("No attendance records found for this course yet.")
        return

    df = pd.DataFrame(report)
    st.dataframe(df, use_container_width=True)

    csv_data = dataframe_to_csv_download(df)
    st.download_button(
        "Download Course Report CSV",
        data=csv_data,
        file_name=f"{selected_course_code}_attendance_report.csv",
        mime="text/csv",
    )


def show_admin_manage_users():
    st.markdown('<div class="main-title">Manage User Accounts</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Students", "Lecturers"])

    # ----------------------------------------------------------
    # STUDENTS TAB
    # ----------------------------------------------------------
    with tab1:
        st.markdown("### Student Accounts")

        students = get_all_students_with_status()

        if not students:
            st.info("No students found.")
        else:
            for student in students:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    st.write(f"**{student['first_name']} {student['last_name']}**")
                    st.caption(f"{student['matric_no']} · {student['username']} · {student['department_name']}")

                with col2:
                    if student["is_active"]:
                        st.success("Active")
                    else:
                        st.error("Inactive")

                with col3:
                    if student["is_active"]:
                        if st.button(
                            "Deactivate",
                            key=f"deactivate_student_{student['user_id']}",
                        ):
                            try:
                                set_user_active_status(student["user_id"], False)
                                st.warning(f"{student['first_name']} {student['last_name']} deactivated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        if st.button(
                            "Activate",
                            key=f"activate_student_{student['user_id']}",
                        ):
                            try:
                                set_user_active_status(student["user_id"], True)
                                st.success(f"{student['first_name']} {student['last_name']} activated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                with col4:
                    if st.button(
                        "Delete",
                        key=f"delete_student_{student['user_id']}",
                        type="primary",
                    ):
                        try:
                            delete_user(student["user_id"])
                            st.success(f"Student {student['matric_no']} deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                st.divider()

    # ----------------------------------------------------------
    # LECTURERS TAB
    # ----------------------------------------------------------
    with tab2:
        st.markdown("### Lecturer Accounts")

        lecturers = get_all_lecturers_with_status()

        if not lecturers:
            st.info("No lecturers found.")
        else:
            for lecturer in lecturers:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    st.write(f"**{lecturer['first_name']} {lecturer['last_name']}**")
                    st.caption(f"{lecturer['staff_no']} · {lecturer['username']} · {lecturer['department_name']}")

                with col2:
                    if lecturer["is_active"]:
                        st.success("Active")
                    else:
                        st.error("Inactive")

                with col3:
                    if lecturer["is_active"]:
                        if st.button(
                            "Deactivate",
                            key=f"deactivate_lecturer_{lecturer['user_id']}",
                        ):
                            try:
                                set_user_active_status(lecturer["user_id"], False)
                                st.warning(f"{lecturer['first_name']} {lecturer['last_name']} deactivated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        if st.button(
                            "Activate",
                            key=f"activate_lecturer_{lecturer['user_id']}",
                        ):
                            try:
                                set_user_active_status(lecturer["user_id"], True)
                                st.success(f"{lecturer['first_name']} {lecturer['last_name']} activated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                with col4:
                    if st.button(
                        "Delete",
                        key=f"delete_lecturer_{lecturer['user_id']}",
                        type="primary",
                    ):
                        try:
                            delete_user(lecturer["user_id"])
                            st.success(f"Lecturer {lecturer['staff_no']} deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                st.divider()


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

def public_sidebar():
    st.sidebar.title("SIBAS")
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Login", "Help & Support"],
    )
    st.session_state.selected_page = page


def logged_in_sidebar():
    user = st.session_state.user
    role = user["role_name"]

    st.sidebar.title("SIBAS")
    st.sidebar.write(f"Logged in as: **{user['username']}**")
    st.sidebar.write(f"Role: **{role}**")

    if role == "Student":
        page = st.sidebar.radio(
            "Student Menu",
            ["Dashboard", "My Profile", "Help & Support"],
        )

    elif role == "Lecturer":
        page = st.sidebar.radio(
            "Lecturer Menu",
            [
                "Dashboard",
                "Upload Attendance",
                "Correct Attendance",
                "Course Reports",
                "Help & Support",
            ],
        )

    elif role == "Administrator":
        page = st.sidebar.radio(
            "Admin Menu",
            [
                "Dashboard",
                "Create Student",
                "Create Lecturer",
                "Manage Academics",
                "Bulk Student Upload",
                "Students",
                "Lecturers",
                "Courses",
                "Reports",
                "Manage Users",
                "Help & Support",
            ],
        )

    else:
        page = "Help & Support"

    if st.sidebar.button("Logout"):
        logout()

    st.session_state.selected_page = page


# ============================================================
# MAIN ROUTER
# ============================================================

if not st.session_state.logged_in:
    public_sidebar()

    if st.session_state.selected_page == "Home":
        show_home_page()
    elif st.session_state.selected_page == "Login":
        show_login_page()
    elif st.session_state.selected_page == "Help & Support":
        show_help_page()

else:
    logged_in_sidebar()

    user_role = st.session_state.user["role_name"]
    selected_page = st.session_state.selected_page

    if user_role == "Student":
        if selected_page == "Dashboard":
            show_student_dashboard()
        elif selected_page == "My Profile":
            show_student_profile()
        elif selected_page == "Help & Support":
            show_help_page()

    elif user_role == "Lecturer":
        if selected_page == "Dashboard":
            show_lecturer_dashboard()
        elif selected_page == "Upload Attendance":
            show_attendance_upload_page()
        elif selected_page == "Correct Attendance":
            show_correct_attendance_page()
        elif selected_page == "Course Reports":
            show_lecturer_course_report()
        elif selected_page == "Help & Support":
            show_help_page()

    elif user_role == "Administrator":
        if selected_page == "Dashboard":
            show_admin_dashboard()
        elif selected_page == "Create Student":
            show_admin_create_student()
        elif selected_page == "Create Lecturer":
            show_admin_create_lecturer()
        elif selected_page == "Manage Academics":
            show_admin_manage_academics()
        elif selected_page == "Bulk Student Upload":
            show_admin_student_upload()
        elif selected_page == "Students":
            show_admin_students()
        elif selected_page == "Lecturers":
            show_admin_lecturers()
        elif selected_page == "Courses":
            show_admin_courses()
        elif selected_page == "Reports":
            show_admin_reports()
        elif selected_page == "Manage Users":
            show_admin_manage_users()
        elif selected_page == "Help & Support":
            show_help_page()

    else:
        st.error("Unknown role. Please contact the administrator.")
