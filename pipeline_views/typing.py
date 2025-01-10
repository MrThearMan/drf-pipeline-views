from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Generator,
    Iterable,
    Literal,
    Optional,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeGuard,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.serializers import Serializer

    from .views import BasePipelineView


__all__ = [
    "Any",
    "Callable",
    "ClassVar",
    "Generator",
    "Iterable",
    "Literal",
    "Optional",
    "ParamSpec",
    "Protocol",
    "TypeAlias",
    "TypeGuard",
    "TypeVar",
    "TypedDict",
    "Union",
]


DataDict: TypeAlias = dict[str, Any]
SerializerType: TypeAlias = type["Serializer"]
DataConditional: TypeAlias = tuple[Any, DataDict]
DataReturn: TypeAlias = Union[DataDict, DataConditional, None]
HTTPMethod: TypeAlias = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable: TypeAlias = Callable[..., DataReturn]
PipelineLogic: TypeAlias = Union[LogicCallable, SerializerType, Iterable["PipelineLogic"]]
PipelinesDict: TypeAlias = dict[HTTPMethod, PipelineLogic]


class GenericView(Protocol):
    def __call__(self: BasePipelineView, request: "Request", *args: Any, **kwargs: Any) -> "Response": ...


class ViewContext(TypedDict):
    request: "Request"
    format: str
    view: BasePipelineView
