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
        Set,
        Tuple,
        Type,
        TypedDict,
        TypeVar,
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
        TypeVar,
        Set,
    )
    from typing_extensions import (  # type: ignore
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
    "T",
    "Set",
]


T = TypeVar("T")  # pylint: disable=C0103
DataDict = Dict[str, Any]
SerializerType = Type[BaseSerializer]
DataConditional = Tuple[Any, DataDict]
DataReturn = Union[DataDict, DataConditional, None]
HTTPMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable = Callable[..., DataReturn]
PipelineLogic = Union[LogicCallable, SerializerType, Iterable["PipelineLogic"]]  # type: ignore
PipelinesDict = Dict[HTTPMethod, PipelineLogic]  # type: ignore
TypesDict = Dict[str, Union[Optional[Type], "TypesDict"]]  # type: ignore


class ViewContext(TypedDict):
    request: Request
    format: str
    view: "BaseAPIView"
