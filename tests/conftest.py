import os

import pytest
from django.http import HttpRequest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.request import Request
from rest_framework.serializers import ListSerializer, Serializer

from pipeline_views.typing import Any, Dict, TypedDict
from pipeline_views.views import BasePipelineView


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.django.settings")


class TestType(TypedDict):
    x: int


@pytest.fixture(scope="session", autouse=True)
def setup_django_settings() -> SettingsWrapper:
    wrapper = SettingsWrapper()
    wrapper.DEBUG = False
    wrapper.LANGUAGE_CODE = "en-us"
    wrapper.LANGUAGES = [("en", "English"), ("fi", "Finland")]

    yield wrapper
    wrapper.finalize()


@pytest.fixture()
def drf_request() -> Request:
    return Request(HttpRequest())


@pytest.fixture()
def base_api_view(drf_request) -> BasePipelineView:
    view = BasePipelineView()
    view.request = drf_request
    view.format_kwarg = None
    return view


def to_comparable_dict(serializer: Serializer) -> Dict[str, Any]:
    d = {}
    is_list = isinstance(serializer, ListSerializer)
    fields = serializer.child.fields if is_list else serializer.fields
    for name, field in fields.items():
        if isinstance(field, ListSerializer):
            d[name] = [to_comparable_dict(field.child)]
        elif isinstance(field, Serializer):
            d[name] = to_comparable_dict(field)
        else:
            d[name] = str(field)
    return [d] if is_list else d
