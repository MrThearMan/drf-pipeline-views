import asyncio
from time import sleep

import pytest
from django.http import HttpRequest
from django.utils.translation import get_language as which_language
from rest_framework.request import Request

from pipeline_views import BasePipelineView
from pipeline_views.utils import cache_pipeline_logic, get_language, get_view_method, run_in_thread, translate


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
    assert get_language(drf_request) == "en-us"


def test_get_language__defaults_to_english__language_not_available(drf_request):
    drf_request._request.GET[b"lang"] = b"ru"
    drf_request.LANGUAGE_CODE = "hi"

    assert get_language(drf_request) == "en-us"


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


def test_cache_pipeline_logic():
    count = 0

    def couter():
        nonlocal count
        count += 1

    @cache_pipeline_logic(cache_key="foo", timeout=2)
    async def test():
        couter()
        return "x"

    asyncio.run(test())
    asyncio.run(test())

    assert count == 1, "Cache should have bypassed the second call to counter"


def test_cache_pipeline_logic__cache_expired():
    count = 0

    def couter():
        nonlocal count
        count += 1

    @cache_pipeline_logic(cache_key="bar", timeout=1)
    async def test():
        couter()
        return "y"

    asyncio.run(test())
    sleep(1.1)
    asyncio.run(test())

    assert count == 2, "Cache should have expired, and the second call made"


def test_run_in_a_thread():
    @run_in_thread
    def callable_1():
        return {"testing", 123}

    result = callable_1()
    assert result == {"testing", 123}


def test_get_view_method__get(drf_request):
    data = None

    def caller(**kwargs):
        nonlocal data
        data = kwargs

    class TestView(BasePipelineView):
        pipelines = {"GET": [caller]}

    drf_request._request.GET[b"key"] = b"value"

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "GET"
    view.get(drf_request)

    assert data == {"key": "value"}


def test_get_view_method__post(drf_request):
    data = None

    def caller(**kwargs):
        nonlocal data
        data = kwargs

    class TestView(BasePipelineView):
        pipelines = {"POST": [caller]}

    drf_request._data = drf_request._full_data = {"key": "value"}

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "POST"
    view.post(drf_request)

    assert data == {"key": "value"}


def test_get_view_method__put(drf_request):
    data = None

    def caller(**kwargs):
        nonlocal data
        data = kwargs

    class TestView(BasePipelineView):
        pipelines = {"PUT": [caller]}

    drf_request._data = drf_request._full_data = {"key": "value"}

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "PUT"
    view.put(drf_request)

    assert data == {"key": "value"}


def test_get_view_method__patch(drf_request):
    data = None

    def caller(**kwargs):
        nonlocal data
        data = kwargs

    class TestView(BasePipelineView):
        pipelines = {"PATCH": [caller]}

    drf_request._data = drf_request._full_data = {"key": "value"}

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "PATCH"
    view.patch(drf_request)

    assert data == {"key": "value"}


def test_get_view_method__delete(drf_request):
    data = None

    def caller(**kwargs):
        nonlocal data
        data = kwargs

    class TestView(BasePipelineView):
        pipelines = {"DELETE": [caller]}

    drf_request._data = drf_request._full_data = {"key": "value"}

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "DELETE"
    view.delete(drf_request)

    assert data == {"key": "value"}
