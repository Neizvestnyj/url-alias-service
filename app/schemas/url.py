from datetime import datetime
from typing import Annotated

from pydantic import AnyUrl as _AnyUrlBase, BaseModel, BeforeValidator, TypeAdapter

_AnyUrlAdapter = TypeAdapter(_AnyUrlBase)

# AnyUrl — это строка, перед валидацией которой вызывается BeforeValidator,
# который преобразует значение к str, предварительно проверив его как URL
AnyUrl = Annotated[str, BeforeValidator(lambda v: str(_AnyUrlAdapter.validate_python(v)))]


class URLBase(BaseModel):
    """
    Базовая схема для URL.

    :param original_url: Исходный URL.
    :type original_url: str
    """

    original_url: AnyUrl


class URLCreate(URLBase):
    """
    Схема для создания короткой ссылки.

    :param short_key: Пользовательский короткий ключ (опционально).
    :type short_key: str | None
    """

    short_key: str | None = None


class URLResponse(URLBase):
    """
    Схема для ответа с данными о короткой ссылке.

    :param id: Идентификатор записи.
    :type id: int
    :param short_key: Короткий ключ.
    :type short_key: str
    :param is_active: Активна ли ссылка.
    :type is_active: bool
    :param expires_at: Дата истечения срока действия.
    :type expires_at: datetime
    :param created_at: Дата создания.
    :type created_at: datetime
    :param click_count: Количество переходов.
    :type click_count: int
    :param user_id: Идентификатор владельца URL.
    :type user_id: int
    """

    id: int
    short_key: str
    is_active: bool
    expires_at: datetime
    created_at: datetime
    click_count: int
    user_id: int

    model_config = {"from_attributes": True}
