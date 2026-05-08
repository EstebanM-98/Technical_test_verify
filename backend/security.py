from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify with bcrypt. Falls back to plaintext comparison for backward compat."""
    try:
        return _pwd_context.verify(plain, hashed)
    except ValueError:
        return plain == hashed
