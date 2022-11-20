from datetime import date, datetime, time, timedelta
from decimal import Decimal
from inspect import getfullargspec

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
    JSONField,
    ListField,
    TimeField,
)
from rest_framework.serializers import BaseSerializer, ListSerializer, Serializer

from .serializers import MockSerializer
from .typing import (
    Any,
    Callable,
    Dict,
    ForwardRef,
    List,
    Optional,
    Tuple,
    Type,
    TypesDict,
    Union,
    eval_type,
    get_args,
    get_origin,
)


__all__ = [
    "inline_serializer",
    "serializer_from_callable",
    "snake_case_to_camel_case",
    "snake_case_to_pascal_case",
]


def serializer_from_callable(func: Callable[..., Any], output: bool = False) -> Type[MockSerializer]:
    """Create a serializer from the parameter type hints of a callable.
    Attempt to infer the types from the default arguments if no typing information is available.
    If output is true, infer from callable return type.
    In this case, return type should be a TypedDict so that field conversion works.
    """
    types = _return_types(func) if output else _parameter_types(func)
    is_list = isinstance(types, list)
    fields: Dict[str, Field] = _get_fields(types[0]) if is_list else _get_fields(types)
    serializer_name = snake_case_to_pascal_case(f"{func.__name__}_serializer")
    serializer = inline_serializer(serializer_name, super_class=MockSerializer, fields=fields)
    serializer.many = is_list
    return serializer


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
    defaults: Tuple[Any, ...] = args_spec.defaults or ()
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

    globalns = _get_globals(func)
    for name, type_ in types.items():
        types[name] = _unwrap_types(type_, globalns)

    return types


def _return_types(func: Callable[..., Any]) -> Union[TypesDict, List[TypesDict]]:
    """Get the callables return types"""
    func = _unwrap_function(func)
    args_spec = getfullargspec(func)
    return_type = args_spec.annotations.get("return")
    return _unwrap_types(return_type, _get_globals(func))


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
    """Convert types to serializer fields.
    TypedDicts and other classes with __annotations__ dicts
    are recursively converted to serializers based on their types.
    """
    fields: Dict[str, Field] = {}
    for name, type_ in types.items():

        # Could not determine forward referenced TypedDict
        # from another file. This is the best guess.
        if isinstance(type_, ForwardRef):
            fields[name] = JSONField()
            continue

        if isinstance(type_, dict):
            fields[name] = inline_serializer(name, fields=_get_fields(type_))()
            continue

        if isinstance(type_, list):
            if isinstance(type_[0], dict):
                fields[name] = inline_serializer(name, fields=_get_fields(type_[0]))(many=True)
            else:
                fields[name] = ListField(child=_type_to_serializer_field.get(type_[0], CharField)())

            continue

        field = _type_to_serializer_field.get(type_, CharField)
        if issubclass(field, DecimalField):
            fields[name] = field(max_digits=13, decimal_places=3)
            continue

        fields[name] = field()

    return fields


def _unwrap_types(
    types: Union[Type, TypesDict, List[TypesDict]],
    globalns: Dict[str, Any],
) -> Union[Type, TypesDict, List[TypesDict]]:
    """Recurively unwrap types from the given item."""
    typ = _forward_refs_to_types(types, globalns)

    if hasattr(typ, "__origin__"):
        return _unwrap_generic(typ, globalns)

    if not hasattr(typ, "__annotations__"):
        return typ

    annotations: TypesDict = typ.__annotations__
    for name, annotation in annotations.items():
        annotations[name] = _unwrap_types(annotation, globalns)

    return annotations


def _forward_refs_to_types(
    types: Union[Type, TypesDict, List[TypesDict]],
    globalns: Dict[str, Any],
) -> Union[Type, TypesDict, List[TypesDict]]:
    """Convert strings and forward references to types."""
    if isinstance(types, str):
        types = ForwardRef(types)

    if isinstance(types, ForwardRef):
        try:
            types = eval_type(types, globalns, globalns)
        except NameError:
            pass

    if hasattr(types, "__args__"):
        args = []
        for arg in types.__args__:
            args.append(_forward_refs_to_types(arg, globalns))
        types.__args__ = tuple(args)

    return types


def _unwrap_generic(type_: Type, globalns: Dict[str, Any]) -> Union[List[TypesDict], Dict[str, List[TypesDict]], Type]:
    """Ungrap the arguments of generics like list and dicts into proper types."""
    origin_type: Type = get_origin(type_)
    origin_args: Tuple[Type, ...] = get_args(type_)

    if origin_type not in (tuple, list, set, dict):
        return type_

    arg_types = []

    if issubclass(origin_type, dict):
        origin_args = origin_args[1:]

    for arg_type in origin_args:
        if not hasattr(arg_type, "__annotations__"):
            if hasattr(arg_type, "__origin__"):
                arg_type = _unwrap_generic(arg_type, globalns)

            arg_types.append(arg_type)
            continue

        anns = {}
        for name, annotation in arg_type.__annotations__.items():
            anns[name] = _unwrap_types(annotation, globalns)

        arg_types.append(anns)

    if issubclass(origin_type, dict):
        return {"str": arg_types[0]}

    return arg_types


def _unwrap_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """Unwrap decorated functions to allow fetching types from them."""
    while hasattr(func, "__wrapped__"):
        func = func.__wrapped__
    return func


def _get_globals(func: Callable[..., Any]) -> Dict[str, Any]:
    return getattr(_unwrap_function(func), "__globals__", {})


def _to_comparable_dict(serializer: Serializer) -> Dict[str, Any]:
    dct = {}
    is_list = isinstance(serializer, ListSerializer)
    fields = serializer.child.fields if is_list else serializer.fields
    for name, field in fields.items():
        if isinstance(field, ListSerializer):
            dct[name] = [_to_comparable_dict(field.child)]
        elif isinstance(field, Serializer):
            dct[name] = _to_comparable_dict(field)
        else:
            dct[name] = str(field)
    return [dct] if is_list else dct


def snake_case_to_pascal_case(string: str) -> str:
    return "".join([s.capitalize() for s in string.split("_")])


def snake_case_to_camel_case(string: str) -> str:
    words = [s for s in string.split("_") if s]
    return words[0] + "".join(x.title() for x in words[1:])
