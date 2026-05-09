from passlib.context import CryptContext

from logger import get_logger

logger = get_logger(__name__, "backend.log")

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    logger.debug("Hashing password.")
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a plain-text password against a bcrypt hash.
    Falls back to plain-text comparison for backward compatibility
    with legacy records, emitting a warning when the fallback is used.
    """
    try:
        result = _pwd_context.verify(plain, hashed)
        logger.debug("Password verification result: %s", result)
        return result
    except ValueError:
        logger.warning(
            "bcrypt verification failed — falling back to plain-text comparison. "
            "This indicates a legacy password that should be re-hashed on next login."
        )
        return plain == hashed
