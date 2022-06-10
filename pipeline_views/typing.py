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
    from typing import Literal, Protocol, TypedDict
except ImportError:
    from typing_extensions import Literal, Protocol, TypedDict

# New in version 3.10
try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer


if TYPE_CHECKING:
    from .views import BasePipelineView  # pylint: disable=R0401


__all__ = [
    "HTTPMethod",
    "LogicCallable",
    "PipelineLogic",
    "PipelinesDict",
    "ViewContext",
    "TYPE_CHECKING",
    "Any",
    "Callable",
    "Dict",
    "List",
    "Tuple",
    "Iterable",
    "Literal",
    "Optional",
    "Type",
    "TypedDict",
    "Union",
    "Generator",
    "Protocol",
    "DataDict",
    "DataConditional",
    "DataReturn",
    "SerializerType",
    "TypesDict",
    "T",
    "P",
    "Set",
    "Container",
    "ForwardRef",
    "eval_type",
    "Coroutine",
    "ExternalDocs",
    "Sequence",
    "ViewMethod",
    "APIContact",
    "APILicense",
    "APIInfo",
    "APISchema",
]


T = TypeVar("T")  # pylint: disable=C0103
P = ParamSpec("P")  # pylint: disable=C0103
eval_type = _eval_type
DataDict = Dict[str, Any]
SerializerType = Type[BaseSerializer]
DataConditional = Tuple[Any, DataDict]
DataReturn = Union[DataDict, DataConditional, None]
HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable = Callable[..., DataReturn]
PipelineLogic = Union[LogicCallable, SerializerType, Iterable["PipelineLogic"]]  # type: ignore
PipelinesDict = Dict[HTTPMethod, PipelineLogic]  # type: ignore
TypesDict = Dict[str, Union[Optional[Type], "TypesDict"]]  # type: ignore


class ViewMethod(Protocol):
    def __call__(self: "BasePipelineView", request: Request, *args: Any, **kwargs: Any) -> Response:
        """..."""


class ViewContext(TypedDict):
    request: Request
    format: str
    view: "BasePipelineView"


class ExternalDocs(TypedDict):
    description: str
    url: str


class APIContact(TypedDict, total=False):
    name: str
    url: str
    email: str


class APILicense(TypedDict, total=False):
    name: str
    url: str


class APIInfo(TypedDict, total=False):
    title: str
    version: str
    description: str
    contact: APIContact
    license: APILicense
    termsOfService: str


class APISchema(TypedDict, total=False):
    openapi: str
    info: APIInfo
    paths: Dict[str, Dict[str, Any]]
    components: Dict[str, Dict[str, Any]]
    security: List[Dict[str, List[Any]]]
    tags: List[Dict[str, Any]]
    externalDocs: ExternalDocs
    servers: List[Dict[str, Any]]
