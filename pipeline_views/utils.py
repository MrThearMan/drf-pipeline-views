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
from rest_framework.serializers import Serializer

from .serializers import MockSerializer
from .typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Type, Union


__all__ = [
    "get_language",
    "translate",
    "parameter_types",
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


def parameter_types(func: Callable[..., Any]) -> Dict[str, Optional[Type]]:
    """Get the types for a callable's parameters."""
    args_spec = getfullargspec(func)
    types = args_spec.annotations

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

    return types


def serializer_from_callable(func: Callable[..., Any]) -> Type[MockSerializer]:
    """Create a serializer from the parameter type hints of a callable.
    Attempt to infer the types from the default arguments if no typing information is available.
    """
    types = parameter_types(func)

    fields: Dict[str, Field] = {}
    for name, type_ in types.items():
        field = type_to_serializer_field.get(type_, CharField)
        if issubclass(field, DecimalField):
            fields[name] = field(max_digits=13, decimal_places=3)
            continue
        fields[name] = field()

    serializer_name = snake_case_to_pascal_case(f"{func.__name__}_serializer")
    return inline_serializer(serializer_name, super_class=MockSerializer, fields=fields)


def inline_serializer(
    name: str,
    super_class: Type[Serializer] = Serializer,
    fields: Dict[str, Field] = None,
) -> Type[Serializer]:
    return type(name, (super_class,), fields or {})  # type: ignore
