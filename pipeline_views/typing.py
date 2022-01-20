try:
    from typing import (  # type: ignore
        TYPE_CHECKING,
        Any,
        Callable,
        Coroutine,
        Dict,
        ForwardRef,
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
        _eval_type,
    )
except ImportError:
    from typing import (  # type: ignore
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
        ForwardRef,
        Coroutine,
        _eval_type,
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
    "ForwardRef",
    "eval_type",
    "CallableAny",
    "Coroutine",
    "CoroutineCallable",
]


T = TypeVar("T")  # pylint: disable=C0103
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
CoroutineCallable = Callable[..., Coroutine[Any, Any, T]]
CallableAny = Callable[..., T]


class ViewContext(TypedDict):
    request: Request
    format: str
    view: "BaseAPIView"
