from pydantic import BaseModel


class UserBase(BaseModel):
    """
    Базовая схема для пользователя.

    :param username: Имя пользователя.
    :type username: str
    """

    username: str


class UserCreate(UserBase):
    """
    Схема для создания пользователя.

    :param password: Пароль пользователя.
    :type password: str
    """

    password: str


class UserResponse(UserBase):
    """
    Схема для ответа с данными о пользователе.

    :param id: Идентификатор пользователя.
    :type id: int
    :param hashed_password: Захэшированный пароль пользователя.
    :type hashed_password: str
    """

    id: int
    hashed_password: str

    model_config = {"from_attributes": True}
