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
from rest_framework.serializers import Serializer


if TYPE_CHECKING:
    from .views import BaseAPIView  # pylint: disable=R0401


__all__ = [
    "MethodType",
    "LogicCallable",
    "PipelineLogic",
    "PipelineDefinition",
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
]

DataDict = Dict[str, Any]
DataConditional = Tuple[Any, DataDict]
DataReturn = Union[DataDict, DataConditional]
MethodType = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable = Callable[..., Optional[DataReturn]]
PipelineLogic = Union[LogicCallable, Iterable["PipelineLogic"]]
PipelineDefinition = Iterable[Union[PipelineLogic, Type[Serializer]]]
PipelinesDict = Dict[MethodType, PipelineDefinition]


class ViewContext(TypedDict):
    request: Request
    format: str
    view: "BaseAPIView"
