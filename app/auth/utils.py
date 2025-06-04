from passlib.context import CryptContext

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.

    :param password: Пароль в открытом виде.
    :type password: str
    :returns: Хешированный пароль.
    :rtype: str
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хешу.

    :param plain_password: Пароль в открытом виде.
    :type plain_password: str
    :param hashed_password: Хешированный пароль.
    :type hashed_password: str
    :returns: True, если пароль соответствует хешу, иначе False.
    :rtype: bool
    """
    return pwd_context.verify(plain_password, hashed_password)
