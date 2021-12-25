from time import sleep

import pytest
from django.http import HttpRequest
from django.utils.translation import get_language as which_language
from rest_framework import fields
from rest_framework.request import Request
from rest_framework.serializers import Serializer

from pipeline_views.serializers import MockSerializer
from pipeline_views.typing import List, TypedDict
from pipeline_views.utils import (
    cache_pipeline_logic,
    get_language,
    inline_serializer,
    parameter_types,
    run_in_thread,
    serializer_from_callable,
    snake_case_to_pascal_case,
    translate,
)

from .arg_spec_functions import *


def test_parameter_types():
    assert parameter_types(function_01) == {"name": None, "age": None}
    assert parameter_types(function_02) == {"name": int, "age": None}
    assert parameter_types(function_03) == {"name": None, "age": int}
    assert parameter_types(function_04) == {"name": int, "age": int}
    assert parameter_types(function_05) == {"name": None, "age": float}
    assert parameter_types(function_06) == {"name": int, "age": float}
    assert parameter_types(function_07) == {"name": None, "age": int}
    assert parameter_types(function_08) == {"name": int, "age": int}
    assert parameter_types(function_09) == {"name": float, "age": float}
    assert parameter_types(function_10) == {"name": int, "age": float}
    assert parameter_types(function_11) == {"name": float, "age": int}
    assert parameter_types(function_12) == {"name": int, "age": int}
    assert parameter_types(function_13) == {"name": None, "age": None}
    assert parameter_types(function_14) == {"name": int, "age": None}
    assert parameter_types(function_15) == {"name": None, "age": int}
    assert parameter_types(function_16) == {"name": int, "age": int}
    assert parameter_types(function_17) == {"name": None, "age": float}
    assert parameter_types(function_18) == {"name": int, "age": float}
    assert parameter_types(function_19) == {"name": None, "age": int}
    assert parameter_types(function_20) == {"name": int, "age": int}
    assert parameter_types(function_21) == {"name": float, "age": float}
    assert parameter_types(function_22) == {"name": int, "age": float}
    assert parameter_types(function_23) == {"name": float, "age": int}
    assert parameter_types(function_24) == {"name": int, "age": int}
    assert parameter_types(function_25) == {"name": None}
    assert parameter_types(function_26) == {"name": int}
    assert parameter_types(function_27) == {"name": None}
    assert parameter_types(function_28) == {"name": int}
    assert parameter_types(function_29) == {"name": None}
    assert parameter_types(function_30) == {"name": int}
    assert parameter_types(function_31) == {"name": None}
    assert parameter_types(function_32) == {"name": int}
    assert parameter_types(function_33) == {"name": float}
    assert parameter_types(function_34) == {"name": int}
    assert parameter_types(function_35) == {"name": float}
    assert parameter_types(function_36) == {"name": int}
    assert parameter_types(function_37) == {"name": None}
    assert parameter_types(function_38) == {"name": int}
    assert parameter_types(function_39) == {"name": None}
    assert parameter_types(function_40) == {"name": int}
    assert parameter_types(function_41) == {"name": None}
    assert parameter_types(function_42) == {"name": int}
    assert parameter_types(function_43) == {"name": None}
    assert parameter_types(function_44) == {"name": int}
    assert parameter_types(function_45) == {"name": float}
    assert parameter_types(function_46) == {"name": int}
    assert parameter_types(function_47) == {"name": float}
    assert parameter_types(function_48) == {"name": int}
    assert parameter_types(function_49) == {"name": float}
    assert parameter_types(function_50) == {"name": int}
    assert parameter_types(function_51) == {"name": float}
    assert parameter_types(function_52) == {"name": int}
    assert parameter_types(function_53) == {"name": None, "age": None}
    assert parameter_types(function_54) == {"name": int, "age": None}
    assert parameter_types(function_55) == {"name": None, "age": int}
    assert parameter_types(function_56) == {"name": int, "age": int}
    assert parameter_types(function_57) == {"name": float, "age": None}
    assert parameter_types(function_58) == {"name": int, "age": None}
    assert parameter_types(function_59) == {"name": float, "age": int}
    assert parameter_types(function_60) == {"name": int, "age": int}
    assert parameter_types(function_61) == {"name": None, "age": float}
    assert parameter_types(function_62) == {"name": int, "age": float}
    assert parameter_types(function_63) == {"name": None, "age": int}
    assert parameter_types(function_64) == {"name": int, "age": int}


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


def test_get_language__from_language_code(drf_request):
    drf_request.LANGUAGE_CODE = "fi"
    assert get_language(drf_request) == "fi"


def test_get_language__from_lang_query_parameter(drf_request):
    drf_request._request.GET[b"lang"] = b"fi"
    assert get_language(drf_request) == "fi"


def test_get_language__query_parameter_overrides_language_code(drf_request):
    drf_request._request.GET[b"lang"] = b"fi"
    drf_request.LANGUAGE_CODE = "en"
    assert get_language(drf_request) == "fi"


def test_get_language__defaults_to_english__no_language_code(drf_request):
    assert get_language(drf_request) == "en"


def test_get_language__defaults_to_english__language_not_available(drf_request):
    drf_request._request.GET[b"lang"] = b"ru"
    drf_request.LANGUAGE_CODE = "hi"

    assert get_language(drf_request) == "en"


def test_translate__as_decorator(drf_request):
    drf_request.LANGUAGE_CODE = "fi"

    @translate
    def testing(req: Request):
        return str(which_language())

    assert testing(drf_request) == "fi"

    assert str(which_language()) == "en-us"


def test_translate__as_decorator__no_request_parameter():
    @translate
    def testing(x: int):
        return str(which_language())

    with pytest.raises(ValueError):
        testing(1)


def test_translate__as_context_manager(drf_request):
    _request = Request(HttpRequest())
    _request.LANGUAGE_CODE = "fi"

    assert str(which_language()) == "en-us"

    with translate(_request):
        assert str(which_language()) == "fi"


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
    assert snake_case_to_pascal_case("logic_method") == "LogicMethod"


def test_snake_case_to_pascal_case__extra_underscore():
    assert snake_case_to_pascal_case("logic_method_") == "LogicMethod"


def test_cache_pipeline_logic():
    count = 0

    def couter():
        nonlocal count
        count += 1

    @cache_pipeline_logic(cache_key="foo", timeout=2)
    def test():
        couter()
        return "x"

    test()
    test()

    assert count == 1, "Cache should have bypassed the second call to counter"


def test_cache_pipeline_logic__cache_expired():
    count = 0

    def couter():
        nonlocal count
        count += 1

    @cache_pipeline_logic(cache_key="bar", timeout=1)
    def test():
        couter()
        return "y"

    test()
    sleep(1.1)
    test()

    assert count == 2, "Cache should have expired, and the second call made"


def test_run_in_a_thread():
    @run_in_thread
    def callable_1():
        return {"testing", 123}

    result = callable_1()
    assert result == {"testing", 123}
