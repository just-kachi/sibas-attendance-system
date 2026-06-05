import psycopg2
import bcrypt


DB_NAME = "sibas_db"
DB_USER = "postgres"
DB_PASSWORD = "kachi123"
DB_HOST = "localhost"
DB_PORT = "5433"


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


def create_test_admin():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "SELECT role_id FROM roles WHERE role_name = %s",
            ("Administrator",),
        )
        role = cursor.fetchone()

        if role is None:
            raise ValueError("Administrator role does not exist.")

        admin_role_id = role[0]

        username = "admin1"
        email = "admin1@pau.edu.ng"
        password = "password123"
        password_hash = hash_password(password)

        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email),
        )
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user[0]
            print(f"Admin user already exists with user_id: {user_id}")
        else:
            cursor.execute(
                """
                INSERT INTO users (role_id, username, email, password_hash)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id
                """,
                (admin_role_id, username, email, password_hash),
            )
            user_id = cursor.fetchone()[0]
            print(f"Created admin user with user_id: {user_id}")

        cursor.execute(
            "SELECT admin_id FROM administrators WHERE user_id = %s",
            (user_id,),
        )
        existing_admin = cursor.fetchone()

        if existing_admin:
            print(f"Admin profile already exists with admin_id: {existing_admin[0]}")
        else:
            cursor.execute(
                """
                INSERT INTO administrators (
                    user_id,
                    first_name,
                    last_name,
                    phone_number
                )
                VALUES (%s, %s, %s, %s)
                RETURNING admin_id
                """,
                (
                    user_id,
                    "System",
                    "Administrator",
                    "08000000001",
                ),
            )
            admin_id = cursor.fetchone()[0]
            print(f"Created admin profile with admin_id: {admin_id}")

        connection.commit()
        cursor.close()

        print("\nAdmin setup completed successfully.")
        print("Login details:")
        print("Username: admin1")
        print("Password: password123")

    except Exception as error:
        connection.rollback()
        print(f"Error: {error}")

    finally:
        connection.close()


if __name__ == "__main__":
    create_test_admin()