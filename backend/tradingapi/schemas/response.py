from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pageSize: int

class APIResponse(BaseModel, Generic[T]):
    data: Optional[T] = Field(None, description="响应数据")
    message: str = Field("", description="响应消息")
    code: int = Field(0, description="响应代码")

    @classmethod
    def success(cls, data: T = None, message: str = "ok"):
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(cls, message: str = "error", code: int = -1, data={}):
        return cls(code=code, message=message, data=data)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""

    items: list[T] = Field(..., description="数据列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class QueryFilter:
    """查询过滤器"""

    def __init__(self):
        self.conditions = []
        self.order_by = []

    def add_condition(self, condition):
        """添加查询条件"""
        self.conditions.append(condition)
        return self

    def add_order(self, column, desc: bool = False):
        """添加排序"""
        if desc:
            self.order_by.append(column.desc())
        else:
            self.order_by.append(column.asc())
        return self
