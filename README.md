# SIBAS Attendance Management System

SIBAS stands for Student Information Biometrics Attendance System. This project is a redesigned attendance management system built with PostgreSQL, Python, and Streamlit.

The system supports three main roles:

- Administrator
- Lecturer
- Student

## Project Features

### Administrator

- Login with username/email and password
- Create students manually
- Register students through bulk CSV upload
- Create lecturers
- Assign lecturers to one or more courses
- Create departments, programmes, and courses
- View students
- Edit student records
- View lecturers
- Edit lecturer records
- View course reports
- Export reports to CSV

### Lecturer

- Login with username/email and password
- View assigned courses
- Upload attendance using CSV
- Correct/override attendance records
- View course attendance reports
- Export course reports to CSV

### Student

- Login with username/email and password
- View profile
- View attendance summary by course
- See attendance percentage
- See eligibility status based on attendance threshold

## Technologies Used

- Python
- Streamlit
- PostgreSQL
- psycopg2
- pandas
- bcrypt

## Folder Structure

```text
DTS 304 Project Folder/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── db/
│   ├── script1_schema.sql
│   ├── script2_student_upload.py
│   ├── script3_attendance_upload.py
│   ├── create_test_admin.py
│   └── create_test_lecturer.py
├── uploads/
│   ├── sample_students.csv
│   └── sample_attendance.csv
└── utils/
    ├── db.py
    ├── auth.py
    ├── security.py
    ├── student_upload.py
    ├── attendance_upload.py
    ├── reports.py
    └── admin.py