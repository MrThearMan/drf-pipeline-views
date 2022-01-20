import sys
from functools import wraps
from typing import List

import pytest
from rest_framework import fields
from rest_framework.serializers import Serializer
from typing_extensions import TypedDict

from pipeline_views import MockSerializer
from pipeline_views.inference import (
    _parameter_types,
    _return_types,
    _snake_case_to_pascal_case,
    inline_serializer,
    serializer_from_callable,
)
from tests.arg_spec_functions import *


class Foo(TypedDict):
    name: str
    age: int


class Bar(TypedDict):
    foo: Foo
    bar: "Foo"


def test_parameter_types():
    assert _parameter_types(function_01) == {"name": None, "age": None}
    assert _parameter_types(function_02) == {"name": int, "age": None}
    assert _parameter_types(function_03) == {"name": None, "age": int}
    assert _parameter_types(function_04) == {"name": int, "age": int}
    assert _parameter_types(function_05) == {"name": None, "age": float}
    assert _parameter_types(function_06) == {"name": int, "age": float}
    assert _parameter_types(function_07) == {"name": None, "age": int}
    assert _parameter_types(function_08) == {"name": int, "age": int}
    assert _parameter_types(function_09) == {"name": float, "age": float}
    assert _parameter_types(function_10) == {"name": int, "age": float}
    assert _parameter_types(function_11) == {"name": float, "age": int}
    assert _parameter_types(function_12) == {"name": int, "age": int}
    assert _parameter_types(function_13) == {"name": None, "age": None}
    assert _parameter_types(function_14) == {"name": int, "age": None}
    assert _parameter_types(function_15) == {"name": None, "age": int}
    assert _parameter_types(function_16) == {"name": int, "age": int}
    assert _parameter_types(function_17) == {"name": None, "age": float}
    assert _parameter_types(function_18) == {"name": int, "age": float}
    assert _parameter_types(function_19) == {"name": None, "age": int}
    assert _parameter_types(function_20) == {"name": int, "age": int}
    assert _parameter_types(function_21) == {"name": float, "age": float}
    assert _parameter_types(function_22) == {"name": int, "age": float}
    assert _parameter_types(function_23) == {"name": float, "age": int}
    assert _parameter_types(function_24) == {"name": int, "age": int}
    assert _parameter_types(function_25) == {"name": None}
    assert _parameter_types(function_26) == {"name": int}
    assert _parameter_types(function_27) == {"name": None}
    assert _parameter_types(function_28) == {"name": int}
    assert _parameter_types(function_29) == {"name": None}
    assert _parameter_types(function_30) == {"name": int}
    assert _parameter_types(function_31) == {"name": None}
    assert _parameter_types(function_32) == {"name": int}
    assert _parameter_types(function_33) == {"name": float}
    assert _parameter_types(function_34) == {"name": int}
    assert _parameter_types(function_35) == {"name": float}
    assert _parameter_types(function_36) == {"name": int}
    assert _parameter_types(function_37) == {"name": None}
    assert _parameter_types(function_38) == {"name": int}
    assert _parameter_types(function_39) == {"name": None}
    assert _parameter_types(function_40) == {"name": int}
    assert _parameter_types(function_41) == {"name": None}
    assert _parameter_types(function_42) == {"name": int}
    assert _parameter_types(function_43) == {"name": None}
    assert _parameter_types(function_44) == {"name": int}
    assert _parameter_types(function_45) == {"name": float}
    assert _parameter_types(function_46) == {"name": int}
    assert _parameter_types(function_47) == {"name": float}
    assert _parameter_types(function_48) == {"name": int}
    assert _parameter_types(function_49) == {"name": float}
    assert _parameter_types(function_50) == {"name": int}
    assert _parameter_types(function_51) == {"name": float}
    assert _parameter_types(function_52) == {"name": int}
    assert _parameter_types(function_53) == {"name": None, "age": None}
    assert _parameter_types(function_54) == {"name": int, "age": None}
    assert _parameter_types(function_55) == {"name": None, "age": int}
    assert _parameter_types(function_56) == {"name": int, "age": int}
    assert _parameter_types(function_57) == {"name": float, "age": None}
    assert _parameter_types(function_58) == {"name": int, "age": None}
    assert _parameter_types(function_59) == {"name": float, "age": int}
    assert _parameter_types(function_60) == {"name": int, "age": int}
    assert _parameter_types(function_61) == {"name": None, "age": float}
    assert _parameter_types(function_62) == {"name": int, "age": float}
    assert _parameter_types(function_63) == {"name": None, "age": int}
    assert _parameter_types(function_64) == {"name": int, "age": int}


def test_parameter_types__typed_dict():
    def function(foo: "Foo"):
        pass

    assert _parameter_types(function) == {"foo": {"name": str, "age": int}}


def test_parameter_types__typed_dict__decorated():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return {}

        return wrapper

    @decorator
    def function(foo: "Foo"):
        pass

    assert _parameter_types(function) == {"foo": {"name": str, "age": int}}


def test_parameter_types__output__typed_dict():
    def function() -> "Foo":
        pass

    assert _return_types(function) == {"name": str, "age": int}


def test_parameter_types__output__typed_dict__decorated():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return {}

        return wrapper

    @decorator
    def function() -> "Foo":
        pass

    assert _return_types(function) == {"name": str, "age": int}


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Recursice literal evaluation requires Python 3.9 or higher")
def test_parameter_types__typed_dict__recursive():
    def function(foo: "Bar"):
        pass

    assert _parameter_types(function) == {"foo": {"foo": {"name": str, "age": int}, "bar": {"name": str, "age": int}}}


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Recursice literal evaluation requires Python 3.9 or higher")
def test_parameter_types__typed_dict__decorated__recursive():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return {}

        return wrapper

    @decorator
    def function(foo: "Bar"):
        pass

    assert _parameter_types(function) == {"foo": {"foo": {"name": str, "age": int}, "bar": {"name": str, "age": int}}}


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Recursice literal evaluation requires Python 3.9 or higher")
def test_parameter_types__output__typed_dict__recursive():
    def function() -> "Bar":
        pass

    assert _return_types(function) == {"foo": {"name": str, "age": int}, "bar": {"name": str, "age": int}}


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Recursice literal evaluation requires Python 3.9 or higher")
def test_parameter_types__output__typed_dict__decorated__recursive():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return {}

        return wrapper

    @decorator
    def function() -> "Bar":
        pass

    assert _return_types(function) == {"foo": {"name": str, "age": int}, "bar": {"name": str, "age": int}}


def test_serializer_from_callable():
    assert str(serializer_from_callable(function_65)().fields) == str({"x": fields.CharField()})
    assert str(serializer_from_callable(function_66)().fields) == str({"x": fields.IntegerField()})
    assert str(serializer_from_callable(function_67)().fields) == str({"x": fields.FloatField()})
    assert str(serializer_from_callable(function_68)().fields) == str({"x": fields.BooleanField()})
    assert str(serializer_from_callable(function_69)().fields) == str({"x": fields.DictField()})
    assert str(serializer_from_callable(function_70)().fields) == str({"x": fields.ListField()})
    assert str(serializer_from_callable(function_71)().fields) == str({"x": fields.DateField()})
    assert str(serializer_from_callable(function_72)().fields) == str({"x": fields.DateTimeField()})
    assert str(serializer_from_callable(function_73)().fields) == str({"x": fields.TimeField()})
    assert str(serializer_from_callable(function_74)().fields) == str({"x": fields.DurationField()})
    assert str(serializer_from_callable(function_75)().fields) == str(
        {"x": fields.DecimalField(max_digits=13, decimal_places=3)}
    )
    assert str(serializer_from_callable(function_76)().fields) == str({"x": fields.CharField()})
    assert str(serializer_from_callable(function_77)().fields) == str({"x": fields.CharField()})


def test_serializer_from_callable__output():
    class Foo(TypedDict):
        foo: str
        bar: int

    def func1(x: str) -> Foo:
        pass

    def func2(x: str) -> List[Foo]:
        pass

    serializer1 = serializer_from_callable(func1, output=True)
    assert str(serializer1(many=serializer1.many).fields) == str(
        {"foo": fields.CharField(), "bar": fields.IntegerField()}
    )

    serializer2 = serializer_from_callable(func2, output=True)
    assert str(serializer2(many=serializer2.many).child.fields) == str(
        {"foo": fields.CharField(), "bar": fields.IntegerField()}
    )


def test_inline_serializer__defaults():
    inline = inline_serializer("Name")

    assert issubclass(inline, Serializer)
    assert inline().fields == {}
    assert str(inline()) == "Name():"


def test_inline_serializer__subclass_another_serializer():
    inline = inline_serializer("Name", super_class=MockSerializer)

    assert issubclass(inline, MockSerializer)
    assert inline().fields == {}
    assert str(inline()) == "Name():"


def test_inline_serializer__set_attributes():
    inline = inline_serializer("Name", fields={"name": fields.CharField()})

    assert issubclass(inline, Serializer)
    assert str(inline().fields) == str({"name": fields.CharField()})
    assert str(inline()) == "Name():\n    name = CharField()"


def test_snake_case_to_pascal_case():
    assert _snake_case_to_pascal_case("logic_method") == "LogicMethod"


def test_snake_case_to_pascal_case__extra_underscore():
    assert _snake_case_to_pascal_case("logic_method_") == "LogicMethod"
