import pytest
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.fields import CharField, IntegerField

from pipeline_views.serializers import HeaderAndCookieSerializer, MockSerializer


def test_mock_serializer():
    serializer = MockSerializer(data={"testing": 1212})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"testing": 1212}
    assert data == {"testing": 1212}


def test_mock_serializer__subclass__used_like_regular_serializer():
    class SubSerializer(MockSerializer):
        name = CharField()
        age = IntegerField()

    serializer = SubSerializer(data={"name": "John", "age": 26})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"name": "John", "age": 26}
    assert data == {"name": "John", "age": 26}


def test_mock_serializer__subclass__fields_are_skipped():
    class SubSerializer(MockSerializer):
        name = CharField()
        age = IntegerField()

    serializer = SubSerializer(data={"testing": 123, "age": "unknown"})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"testing": 123, "age": "unknown"}
    assert data == {"testing": 123, "age": "unknown"}


def test_header_and_cookie_serializer(drf_request):
    class TestSerializer(HeaderAndCookieSerializer):
        take_from_headers = ["Header-Name"]
        take_from_cookies = ["Cookie-Name"]

    drf_request.META["HTTP_HEADER_NAME"] = "fizz"
    drf_request.COOKIES["Cookie-Name"] = "buzz"
    serializer = TestSerializer(data={}, context={"request": drf_request})
    serializer.is_valid(raise_exception=True)
    validated_data = serializer.validated_data
    data = serializer.data

    assert validated_data == {"header_name": "fizz", "cookie_name": "buzz"}
    assert data == {"header_name": "fizz", "cookie_name": "buzz"}


def test_header_and_cookie_serializer__request_not_found(drf_request):
    class TestSerialzer(HeaderAndCookieSerializer):
        take_from_headers = ["Header-Name"]
        take_from_cookies = ["Cookie-Name"]

    drf_request.META["HTTP_HEADER_NAME"] = "fizz"
    drf_request.COOKIES["Cookie-Name"] = "buzz"
    serializer = TestSerialzer(data={})

    with pytest.raises(ValidationError) as exc_info:
        serializer.is_valid(raise_exception=True)

    assert exc_info.value.args[0] == {
        "non_field_errors": ErrorDetail(
            string="Must include a Request object in the context of the Serializer.",
            code="request_missing",
        )
    }
