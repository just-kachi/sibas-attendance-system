import psycopg2
import bcrypt


DB_NAME = "sibas_db"
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"


def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def get_role_id(cursor, role_name: str):
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name = %s",
        (role_name,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Role '{role_name}' does not exist.")

    return result[0]


def get_department_id(cursor, department_code: str):
    cursor.execute(
        "SELECT department_id FROM departments WHERE department_code = %s",
        (department_code,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Department '{department_code}' does not exist.")

    return result[0]


def get_course_id(cursor, course_code: str):
    cursor.execute(
        "SELECT course_id FROM courses WHERE course_code = %s",
        (course_code,),
    )
    result = cursor.fetchone()

    if result is None:
        raise ValueError(f"Course '{course_code}' does not exist.")

    return result[0]


def create_test_lecturer():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        lecturer_role_id = get_role_id(cursor, "Lecturer")
        department_id = get_department_id(cursor, "CSC")

        username = "lecturer1"
        email = "lecturer1@pau.edu.ng"
        password = "password123"
        password_hash = hash_password(password)

        # Check if lecturer user already exists
        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email),
        )
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user[0]
            print(f"User already exists with user_id: {user_id}")
        else:
            cursor.execute(
                """
                INSERT INTO users (role_id, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
                """,
                (lecturer_role_id, username, email, password_hash),
            )
            user_id = cursor.fetchone()[0]
            print(f"Created lecturer user with user_id: {user_id}")

        # Check if lecturer profile already exists
        cursor.execute(
            "SELECT lecturer_id FROM lecturers WHERE user_id = %s",
            (user_id,),
        )
        existing_lecturer = cursor.fetchone()

        if existing_lecturer:
            lecturer_id = existing_lecturer[0]
            print(f"Lecturer profile already exists with lecturer_id: {lecturer_id}")
        else:
            cursor.execute(
                """
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
                RETURNING lecturer_id
                """,
                (
                    user_id,
                    department_id,
                    "STAFF001",
                    "Test",
                    "Lecturer",
                    email,
                    "08000000000",
                ),
            )
            lecturer_id = cursor.fetchone()[0]
            print(f"Created lecturer profile with lecturer_id: {lecturer_id}")

        # Assign lecturer to courses
        course_codes = ["DTS304", "CSC313"]

        for course_code in course_codes:
            course_id = get_course_id(cursor, course_code)

            cursor.execute(
                """
                INSERT INTO lecturer_courses (
                    lecturer_id,
                    course_id,
                    academic_session,
                    semester
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (lecturer_id, course_id, academic_session, semester)
                DO NOTHING
                """,
                (lecturer_id, course_id, "2025/2026", "Second"),
            )

            print(f"Assigned lecturer to course: {course_code}")

        connection.commit()
        cursor.close()

        print("\nLecturer setup completed successfully.")
        print("Login details for testing:")
        print("Username: lecturer1")
        print("Password: password123")

    except Exception as error:
        connection.rollback()
        print(f"Error: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    create_test_lecturer()
