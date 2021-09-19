from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Literal, Optional, Type, TypedDict, Union

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
]


MethodType = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable = Callable[..., Optional[Dict[str, Any]]]
PipelineLogic = Union[LogicCallable, Iterable[LogicCallable]]
PipelineDefinition = Iterable[Union[PipelineLogic, Type[Serializer]]]
PipelinesDict = Dict[MethodType, PipelineDefinition]


class ViewContext(TypedDict):
    request: Request
    format: str
    view: "BaseAPIView"
