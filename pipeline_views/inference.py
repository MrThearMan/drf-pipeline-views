from datetime import date, datetime, time, timedelta
from decimal import Decimal
from inspect import getfullargspec
from typing import Any, Callable, Dict, ForwardRef, List, Optional, Tuple, Type, Union

from rest_framework.fields import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    DictField,
    DurationField,
    Field,
    FloatField,
    IntegerField,
    ListField,
    TimeField,
)
from rest_framework.serializers import BaseSerializer, Serializer

from .serializers import MockSerializer
from .typing import TypesDict, eval_type


__all__ = [
    "serializer_from_callable",
    "inline_serializer",
]


def serializer_from_callable(func: Callable[..., Any], output: bool = False) -> Type[MockSerializer]:
    """Create a serializer from the parameter type hints of a callable.
    Attempt to infer the types from the default arguments if no typing information is available.
    If output is true, infer from callable return type.
    In this case, return type should be a TypedDict so that field conversion works.
    """
    types = _return_types(func) if output else _parameter_types(func)
    is_list = isinstance(types, list)
    fields: Dict[str, Field] = _get_fields(types[0]) if is_list else _get_fields(types)  # type: ignore
    serializer_name = _snake_case_to_pascal_case(f"{func.__name__}_serializer")
    serializer = inline_serializer(serializer_name, super_class=MockSerializer, fields=fields)
    serializer.many = is_list
    return serializer  # type: ignore


def inline_serializer(
    name: str,
    super_class: Type[BaseSerializer] = Serializer,
    fields: Dict[str, Field] = None,
) -> Type[BaseSerializer]:
    return type(name, (super_class,), fields or {})  # type: ignore


def _parameter_types(func: Callable[..., Any]) -> TypesDict:
    """Get the types for a callable's parameters."""
    func = _unwrap_function(func)
    args_spec = getfullargspec(func)
    types = args_spec.annotations
    types.pop("return", None)

    # Get types based on argument default values
    defaults: Tuple[Any, ...] = args_spec.defaults or tuple()
    for name, value in zip(reversed(args_spec.args), reversed(defaults)):
        if name in types:
            continue
        types[name] = type(value)

    # Get types based on keyword-only argument default values
    defaults_kwonly: Dict[str, Any] = args_spec.kwonlydefaults or {}
    for name, value in defaults_kwonly.items():
        if name in types:
            continue
        types[name] = type(value)

    # Add None for all positional arguments and keyword-only arguments
    # for which a type was not found or could not be inferred
    for name in args_spec.args + args_spec.kwonlyargs:
        if name in types:
            continue
        types[name] = None

    # Remove * and ** parameters from the typing dict
    types.pop(args_spec.varargs or "", None)
    types.pop(args_spec.varkw or "", None)

    for name, type_ in types.items():
        types[name] = _unwrap_types(func, type_)

    return types


def _return_types(func: Callable[..., Any]) -> Union[TypesDict, List[TypesDict]]:
    """Get the callables return types"""
    func = _unwrap_function(func)  # type: ignore
    args_spec = getfullargspec(func)
    return_type: Union[Type, List[Type]] = args_spec.annotations.get("return")  # type: ignore
    is_list = hasattr(return_type, "__args__")
    type_: Type = getattr(return_type, "__args__", [return_type])[0]  # type: ignore
    types: TypesDict = _unwrap_types(func, type_)  # type: ignore
    return [types] if is_list else types


_type_to_serializer_field: Dict[Optional[Type], Type[Field]] = {
    str: CharField,
    int: IntegerField,
    float: FloatField,
    bool: BooleanField,
    dict: DictField,
    list: ListField,
    date: DateField,
    datetime: DateTimeField,
    time: TimeField,
    timedelta: DurationField,
    Decimal: DecimalField,
    None: CharField,
    type: CharField,
}


def _get_fields(types: TypesDict) -> Dict[str, Field]:
    """Convert types to serializer fields. TypedDicts and other classes with __annotations__ dicts
    are recursively converted to serializers based on their types.
    """
    fields: Dict[str, Field] = {}
    for name, type_ in types.items():
        if isinstance(type_, dict):
            fields[name] = inline_serializer(name, fields=_get_fields(type_))()
            continue

        field = _type_to_serializer_field.get(type_, CharField)
        if issubclass(field, DecimalField):
            fields[name] = field(max_digits=13, decimal_places=3)
            continue

        fields[name] = field()

    return fields


def _unwrap_types(func: Any, item: Union[Type, str]) -> Union[TypesDict, Type]:
    """Recurively unwrap types from the given item based on its __annotations__ dict."""
    func = _unwrap_function(func)
    type_: Type = _forward_refs_to_types(func, item)
    if not hasattr(type_, "__annotations__"):
        return type_

    annotations: TypesDict = type_.__annotations__
    for name, annotation in annotations.items():
        annotations[name] = _unwrap_types(type_, annotation)  # type: ignore
    return annotations


def _forward_refs_to_types(item: Any, type_: Union[Type, str]) -> Type:
    """Convert strings and forward references to types."""
    if isinstance(type_, str):
        type_: ForwardRef = ForwardRef(type_)  # type: ignore
    if isinstance(type_, ForwardRef):
        item = _unwrap_function(item)
        globalns = getattr(item, "__globals__", {})
        type_: Type = eval_type(type_, globalns, globalns)  # type: ignore
    return type_  # type: ignore


def _unwrap_function(func):
    """Unwrap decorated functions to allow fetching types from them."""
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


def _snake_case_to_pascal_case(string: str) -> str:
    return "".join([s.capitalize() for s in string.split("_")])
