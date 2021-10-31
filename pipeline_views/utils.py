from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import wraps
from inspect import getfullargspec
from itertools import chain

from django.conf import settings
from django.utils.translation import override
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
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer, Serializer

from .serializers import MockSerializer
from .typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, TypesDict, Union


__all__ = [
    "get_language",
    "translate",
    "is_serializer_class",
    "serializer_from_callable",
    "inline_serializer",
]


available_languages: List[str] = [key for (key, value) in settings.LANGUAGES]


type_to_serializer_field: Dict[Type, Field] = {
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


def is_serializer_class(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, BaseSerializer)


def snake_case_to_pascal_case(string: str) -> str:
    return "".join([s.capitalize() for s in string.split("_")])


def get_language(request: Request) -> str:
    """Get language based on request Accept-Language header or 'lang' query parameter."""
    lang: Optional[str] = request.query_params.get("lang")
    language_code: Optional[str] = getattr(request, "LANGUAGE_CODE", None)

    if lang and lang in available_languages:
        return lang
    if language_code and language_code in available_languages:
        return language_code

    return "en" if "en" in available_languages else available_languages[0]


def translate(item: Union[Callable[..., Any], Request]) -> Union[Generator[Any, Any, None], Callable[..., Any]]:
    """Override current language with one from language header or 'lang' parameter.
    Can be used as a context manager or a decorator. If a function is decorated,
    one of the parameters for the function must be a rest_framework.Request object.
    """

    if not isinstance(item, Request):

        @wraps(item)
        def decorator(*args: Any, **kwargs: Any) -> Any:
            request = None
            for arg in chain(args, kwargs.values()):
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                raise ValueError("No Request-object in function parameters.")

            with override(get_language(request)):
                return item(*args, **kwargs)

        return decorator

    @contextmanager
    def context_manager(request: Request) -> Generator[Any, Any, None]:
        with override(get_language(request)):
            yield

    return context_manager(item)


def _unwrap_types(item: Any) -> Dict:
    """Recurively unwrap types from the given item based on its __annotations__ dict."""
    annotations = item.__annotations__
    for name, annotation in annotations.items():
        if hasattr(annotation, "__annotations__"):
            annotations[name] = _unwrap_types(annotation)
    return annotations


def parameter_types(func: Callable[..., Any]) -> TypesDict:
    """Get the types for a callable's parameters."""
    args_spec = getfullargspec(func)
    types = args_spec.annotations
    types.pop("return", None)

    # Get types based on parameter default values
    defaults: Tuple[Any, ...] = args_spec.defaults or tuple()
    for name, value in zip(reversed(args_spec.args), reversed(defaults)):
        if name in types:
            continue
        types[name] = type(value)

    # Get types based on keyword only parameter default values
    defaults_kwonly: Dict[str, Any] = args_spec.kwonlydefaults or {}
    for name, value in defaults_kwonly.items():
        if name in types:
            continue
        types[name] = type(value)

    # Add None for all parameters and keyword only parameters
    # for which a type was not found or could not be inferred
    for name in args_spec.args + args_spec.kwonlyargs:
        if name in types:
            continue
        types[name] = None

    # Remove * and ** parameters from the typing dict
    types.pop(args_spec.varargs or "", None)
    types.pop(args_spec.varkw or "", None)

    for name, type_ in types.items():
        if hasattr(type_, "__annotations__"):
            types[name] = _unwrap_types(type_)

    return types


def return_types(func: Callable[..., Any]) -> TypesDict:
    """Get the callables return types"""
    args_spec = getfullargspec(func)
    types = args_spec.annotations.get("return")

    if hasattr(types, "__annotations__"):
        types = _unwrap_types(types)

    return types


def get_fields(types: TypesDict) -> Dict[str, Field]:
    """Convert types to serializer fields. TypedDicts and other classes with __annotations__ dicts
    are recursively converted to serializers based on their types.
    """
    fields = {}
    for name, type_ in types.items():
        if isinstance(type_, dict):
            fields[name] = inline_serializer(name, fields=get_fields(type_))()
            continue

        field = type_to_serializer_field.get(type_, CharField)
        if issubclass(field, DecimalField):
            fields[name] = field(max_digits=13, decimal_places=3)
            continue

        fields[name] = field()

    return fields


def serializer_from_callable(func: Callable[..., Any], output: bool = False) -> Type[MockSerializer]:
    """Create a serializer from the parameter type hints of a callable.
    Attempt to infer the types from the default arguments if no typing information is available.
    If output is true, infer from callable return type.
    In this case, return type should be a TypedDict so that field conversion works.
    """
    types = return_types(func) if output else parameter_types(func)
    fields: Dict[str, Field] = get_fields(types)
    serializer_name = snake_case_to_pascal_case(f"{func.__name__}_serializer")
    return inline_serializer(serializer_name, super_class=MockSerializer, fields=fields)


def inline_serializer(
    name: str,
    super_class: Type[BaseSerializer] = Serializer,
    fields: Dict[str, Field] = None,
) -> Type[BaseSerializer]:
    return type(name, (super_class,), fields or {})  # type: ignore
