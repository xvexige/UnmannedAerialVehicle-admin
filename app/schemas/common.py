from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: int = 200
    message: str = "操作成功"
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: T = None, message: str = "操作成功") -> "ResponseModel[T]":
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "ResponseModel":
        return cls(code=code, message=message, data=None)


class PageData(BaseModel, Generic[T]):
    total: int
    page: int
    size: int
    list: list[T]


class PageResponse(ResponseModel[PageData[T]], Generic[T]):
    pass
