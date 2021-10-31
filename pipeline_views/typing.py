try:
    from typing import (
        TYPE_CHECKING,
        Any,
        Callable,
        Dict,
        Generator,
        Iterable,
        List,
        Literal,
        Optional,
        Protocol,
        Tuple,
        Type,
        TypedDict,
        Union,
    )
except ImportError:
    from typing import (
        Any,
        Callable,
        Dict,
        List,
        Tuple,
        Iterable,
        Optional,
        Union,
        Generator,
    )
    from typing_extensions import (
        TYPE_CHECKING,
        Literal,
        Type,
        TypedDict,
        Protocol,
    )

from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer


if TYPE_CHECKING:
    from .views import BaseAPIView  # pylint: disable=R0401


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
]

DataDict = Dict[str, Any]
SerializerType = Type[BaseSerializer]
DataConditional = Tuple[Any, DataDict]
DataReturn = Union[DataDict, DataConditional]
HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable = Callable[..., Optional[DataReturn]]
PipelineLogic = Union[LogicCallable, SerializerType, Iterable["PipelineLogic"]]
PipelinesDict = Dict[HTTPMethod, PipelineLogic]
TypesDict = Dict[str, Union[Optional[Type], "TypesDict"]]


class ViewContext(TypedDict):
    request: Request
    format: str
    view: "BaseAPIView"
