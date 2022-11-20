from __future__ import annotations

from typing import _eval_type  # type: ignore
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Container,
    Coroutine,
    Dict,
    ForwardRef,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)


# New in version 3.8
try:
    from typing import Literal, Protocol, TypedDict, get_args, get_origin
except ImportError:
    from typing_extensions import Literal, Protocol, TypedDict, get_args, get_origin

# New in version 3.9
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

# New in version 3.10
try:
    from typing import ParamSpec, TypeAlias, TypeGuard
except ImportError:
    from typing_extensions import ParamSpec, TypeAlias, TypeGuard

# New in version 3.11
try:
    from typing import NotRequired, Required
except ImportError:
    from typing_extensions import NotRequired, Required

if TYPE_CHECKING:
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.permissions import BasePermission
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.serializers import BaseSerializer

    from ..views import BasePipelineView


__all__ = [
    "Annotated",
    "Any",
    "AuthOrPerm",
    "Callable",
    "Container",
    "Coroutine",
    "DataConditional",
    "DataDict",
    "DataReturn",
    "Dict",
    "eval_type",
    "ForwardRef",
    "Generator",
    "get_args",
    "get_origin",
    "http_method",
    "HTTPMethod",
    "Iterable",
    "List",
    "Literal",
    "LogicCallable",
    "NotRequired",
    "Optional",
    "ParamSpec",
    "PathAndMethod",
    "PipelineLogic",
    "PipelinesDict",
    "Protocol",
    "Required",
    "SchemaCallbackData",
    "SchemaWebhook",
    "SecurityRules",
    "Sequence",
    "SerializerType",
    "Set",
    "Tuple",
    "Type",
    "TYPE_CHECKING",
    "TypeAlias",
    "TypedDict",
    "TypeGuard",
    "TypesDict",
    "TypeVar",
    "Union",
    "ViewContext",
    "ViewMethod",
]


eval_type = _eval_type
DataDict: TypeAlias = Dict[str, Any]
SerializerType: TypeAlias = Type["BaseSerializer"]
DataConditional: TypeAlias = Tuple[Any, DataDict]
DataReturn: TypeAlias = Union[DataDict, DataConditional, None]
HTTPMethod: TypeAlias = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
http_method: TypeAlias = Literal["get", "post", "put", "patch", "delete", "trace", "options"]
LogicCallable: TypeAlias = Callable[..., DataReturn]
PipelineLogic: TypeAlias = Union[LogicCallable, SerializerType, Iterable["PipelineLogic"]]  # type: ignore
PipelinesDict: TypeAlias = Dict[HTTPMethod, PipelineLogic]  # type: ignore
TypesDict: TypeAlias = Dict[str, Union[Optional[Type], "TypesDict"]]  # type: ignore
AuthOrPerm: TypeAlias = Union[Type["BasePermission"], Type["BaseAuthentication"]]
SecurityRules: TypeAlias = Dict[Union[Tuple[AuthOrPerm, ...], AuthOrPerm], Dict[str, List[str]]]


class ViewMethod(Protocol):
    def __call__(self: BasePipelineView, request: Request, *args: Any, **kwargs: Any) -> Response:
        """..."""


class ViewContext(TypedDict):
    request: Request
    format: str
    view: BasePipelineView


class SchemaWebhook(TypedDict):
    method: http_method
    request_data: SerializerType
    responses: Dict[int, Union[str, SerializerType]]


class SchemaLinks(TypedDict):
    method: HTTPMethod
    request_data: SerializerType
    responses: Dict[int, Union[str, SerializerType]]


class SchemaCallbackData(TypedDict):
    request_body: SerializerType
    responses: Dict[int, SerializerType]


class PathAndMethod(TypedDict):
    path: str
    method: HTTPMethod
