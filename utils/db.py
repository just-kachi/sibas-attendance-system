import psycopg2
from psycopg2.extras import RealDictCursor


DB_CONFIG = {
    "dbname": "sibas_db",
    "user": "postgres",
    "password": "kachi123",
    "host": "localhost",
    "port": "5433",
}


def get_connection():
    """
    Creates a connection to the PostgreSQL database.
    """
    return psycopg2.connect(**DB_CONFIG)


def fetch_one(query, params=None):
    """
    Runs a SELECT query and returns one row as a dictionary.
    """
    connection = get_connection()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    finally:
        connection.close()


def fetch_all(query, params=None):
    """
    Runs a SELECT query and returns all rows as dictionaries.
    """
    connection = get_connection()

    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        connection.close()


def execute_query(query, params=None):
    """
    Runs INSERT, UPDATE, or DELETE queries.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_query_returning_id(query, params=None):
    """
    Runs INSERT queries that return an ID.
    """
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            returned_id = cursor.fetchone()[0]
            connection.commit()
            return returned_id
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
