from typing import Generic, TypeVar

from pydantic import BaseModel, field_validator

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @field_validator("page")
    @classmethod
    def page_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_limit(cls, v: int) -> int:
        if not (1 <= v <= 100):
            raise ValueError("page_size must be between 1 and 100")
        return v

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, params: PaginationParams) -> "Page[T]":
        import math
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=math.ceil(total / params.page_size) if total else 0,
        )
