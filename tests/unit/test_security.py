from backend.security import hash_password, verify_password


def test_hash_password_changes_plaintext():
    plain = "secret123"
    hashed = hash_password(plain)
    assert isinstance(hashed, str)
    assert hashed != plain


def test_verify_password_correct_and_wrong():
    plain = "secret123"
    hashed = hash_password(plain)

    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_verify_password_plaintext_fallback():
    assert verify_password("secret", "secret") is True
    assert verify_password("wrong", "secret") is False
