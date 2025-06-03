from passlib.context import CryptContext

from app.auth.utils import get_password_hash, verify_password


def test_get_password_hash() -> None:
    """
    Тестирует хэширование пароля.

    :returns: None
    """
    password: str = "testpass123"
    hashed: str = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > len(password)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    assert pwd_context.verify(password, hashed)


def test_verify_password_correct() -> None:
    """
    Тестирует проверку правильного пароля.

    :returns: None
    """
    password: str = "testpass123"
    hashed: str = get_password_hash(password)
    result: bool = verify_password(password, hashed)
    assert result is True


def test_verify_password_incorrect() -> None:
    """
    Тестирует проверку неправильного пароля.

    :returns: None
    """
    password: str = "testpass123"
    wrong_password: str = "wrongpass"
    hashed: str = get_password_hash(password)
    result: bool = verify_password(wrong_password, hashed)
    assert result is False
