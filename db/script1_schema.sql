-- ============================================================
-- SIBAS — Student Information Biometrics Attendance System
-- Script 1: Database Schema
-- Database: sibas_db
-- ============================================================

-- Create and connect to the database
-- Run this first in psql as a superuser:
--   CREATE DATABASE sibas_db;
--   \c sibas_db

-- ============================================================
-- 1. ROLES
-- ============================================================

CREATE TABLE roles (
    role_id     SERIAL          PRIMARY KEY,
    role_name   VARCHAR(50)     NOT NULL UNIQUE
);

-- Seed the three fixed roles
INSERT INTO roles (role_name) VALUES
    ('Administrator'),
    ('Lecturer'),
    ('Student');


-- ============================================================
-- 2. USERS  (authentication table)
-- ============================================================

CREATE TABLE users (
    user_id         SERIAL          PRIMARY KEY,
    role_id         INTEGER         NOT NULL REFERENCES roles(role_id),
    username        VARCHAR(100)    NOT NULL UNIQUE,
    email           VARCHAR(255)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. ADMINISTRATORS
-- ============================================================

CREATE TABLE administrators (
    admin_id        SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    phone_number    VARCHAR(20),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. DEPARTMENTS
-- ============================================================

CREATE TABLE departments (
    department_id       SERIAL          PRIMARY KEY,
    department_name     VARCHAR(150)    NOT NULL UNIQUE,
    department_code     VARCHAR(20)     NOT NULL UNIQUE,
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 5. PROGRAMMES
-- ============================================================

CREATE TABLE programmes (
    programme_id        SERIAL          PRIMARY KEY,
    department_id       INTEGER         NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    programme_name      VARCHAR(150)    NOT NULL,
    programme_code      VARCHAR(30)     NOT NULL UNIQUE,
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 6. COURSES
-- ============================================================

CREATE TABLE courses (
    course_id       SERIAL          PRIMARY KEY,
    department_id   INTEGER         NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE,
    course_code     VARCHAR(20)     NOT NULL UNIQUE,
    course_title    VARCHAR(200)    NOT NULL,
    credit_units    INTEGER         NOT NULL DEFAULT 3 CHECK (credit_units > 0),
    level           INTEGER         NOT NULL CHECK (level IN (100, 200, 300, 400, 500)),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 7. LECTURERS
-- ============================================================

CREATE TABLE lecturers (
    lecturer_id     SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    department_id   INTEGER         NOT NULL REFERENCES departments(department_id),
    staff_no        VARCHAR(50)     NOT NULL UNIQUE,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    phone_number    VARCHAR(20),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 8. LECTURER–COURSE ASSIGNMENTS  (junction table)
-- ============================================================

CREATE TABLE lecturer_courses (
    lecturer_course_id  SERIAL          PRIMARY KEY,
    lecturer_id         INTEGER         NOT NULL REFERENCES lecturers(lecturer_id) ON DELETE CASCADE,
    course_id           INTEGER         NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    academic_session    VARCHAR(20)     NOT NULL,   -- e.g. '2025/2026'
    semester            VARCHAR(20)     NOT NULL,   -- 'First' | 'Second'
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lecturer_id, course_id, academic_session, semester)
);


-- ============================================================
-- 9. STUDENTS
-- ============================================================

CREATE TABLE students (
    student_id      SERIAL          PRIMARY KEY,
    user_id         INTEGER         NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    department_id   INTEGER         NOT NULL REFERENCES departments(department_id),
    programme_id    INTEGER         NOT NULL REFERENCES programmes(programme_id),
    matric_no       VARCHAR(50)     NOT NULL UNIQUE,
    first_name      VARCHAR(100)    NOT NULL,
    middle_name     VARCHAR(100),
    last_name       VARCHAR(100)    NOT NULL,
    email           VARCHAR(255)    NOT NULL,
    level           INTEGER         NOT NULL CHECK (level IN (100, 200, 300, 400, 500)),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 10. COURSE ENROLLMENTS  (student–course junction table)
-- ============================================================

CREATE TABLE course_enrollments (
    enrollment_id       SERIAL          PRIMARY KEY,
    student_id          INTEGER         NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_id           INTEGER         NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    academic_session    VARCHAR(20)     NOT NULL,
    semester            VARCHAR(20)     NOT NULL,
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    enrolled_at         TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, course_id, academic_session, semester)
);


-- ============================================================
-- 11. ATTENDANCE SESSIONS
-- ============================================================

CREATE TABLE attendance_sessions (
    session_id          SERIAL          PRIMARY KEY,
    course_id           INTEGER         NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    lecturer_id         INTEGER         NOT NULL REFERENCES lecturers(lecturer_id),
    session_date        DATE            NOT NULL,
    topic               VARCHAR(255)    NOT NULL DEFAULT 'Class Attendance',
    academic_session    VARCHAR(20)     NOT NULL,
    semester            VARCHAR(20)     NOT NULL,
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 12. ATTENDANCE RECORDS
-- ============================================================

CREATE TABLE attendance_records (
    record_id       SERIAL          PRIMARY KEY,
    session_id      INTEGER         NOT NULL REFERENCES attendance_sessions(session_id) ON DELETE CASCADE,
    student_id      INTEGER         NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    status          VARCHAR(10)     NOT NULL CHECK (status IN ('Present', 'Absent')),
    uploaded_by     INTEGER         NOT NULL REFERENCES users(user_id),
    updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_id, student_id)
);


-- ============================================================
-- 13. SYSTEM SETTINGS  (configurable threshold etc.)
-- ============================================================

CREATE TABLE system_settings (
    setting_id      SERIAL          PRIMARY KEY,
    setting_name    VARCHAR(100)    NOT NULL UNIQUE,
    setting_value   VARCHAR(255)    NOT NULL,
    updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Seed default attendance threshold (80%)
INSERT INTO system_settings (setting_name, setting_value)
VALUES ('attendance_threshold', '80');


-- ============================================================
-- SEED DATA — departments, programmes, courses for testing
-- ============================================================

-- Departments
INSERT INTO departments (department_name, department_code) VALUES
    ('Computer Science', 'CSC'),
    ('Software Engineering', 'SEN');

-- Programmes
INSERT INTO programmes (department_id, programme_name, programme_code) VALUES
    (1, 'BSc Computer Science',    'BSC-CS'),
    (2, 'BSc Software Engineering','BSC-SE');

-- Courses
INSERT INTO courses (department_id, course_code, course_title, credit_units, level) VALUES
    (1, 'DTS304', 'Data Management I',          3, 300),
    (1, 'CSC313', 'Operating Systems',           3, 300),
    (1, 'CSC309', 'Computer Networks',           3, 300),
    (1, 'CSC310', 'Software Engineering I',      3, 300);
