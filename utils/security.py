import bcrypt


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plain-text password against a stored bcrypt hash.
    """
    try:
        password_bytes = password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False