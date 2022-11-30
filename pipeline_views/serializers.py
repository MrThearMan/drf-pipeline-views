from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.request import Request
from rest_framework.settings import api_settings

from .typing import Any, ClassVar, Dict, List, Optional, Type, Union


__all__ = [
    "CookieSerializerMixin",
    "EmptySerializer",
    "HeaderAndCookieSerializer",
    "HeaderSerializerMixin",
    "MockSerializer",
    "RequestFromContextMixin",
]


class EmptySerializer(serializers.Serializer):
    # Used for schema 204 responses
    pass


class MockSerializer(serializers.Serializer):
    # Serializer that simply passes initial data to output.

    _example: Union[List[Any], Dict[str, Any], Any] = {}

    @classmethod
    def with_example(cls, description: str, response: Union[List[Any], Dict[str, Any], Any]) -> Type["MockSerializer"]:
        """Sets OpenAPI example response."""
        new_cls = type(MockSerializer.__name__, (cls,), {"_example": response})  # type: ignore
        new_cls.__doc__ = description
        return new_cls  # type: ignore

    def to_internal_value(self, data: Any) -> Dict[str, Any]:
        return self.initial_data  # type: ignore

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        return self.initial_data  # type: ignore


class RequestFromContextMixin:
    @cached_property
    def request_from_context(self) -> Request:
        request: Optional[Request] = self.context.get("request")
        if request is None or not isinstance(request, Request):
            raise ValidationError(
                {
                    api_settings.NON_FIELD_ERRORS_KEY: ErrorDetail(
                        string="Must include a Request object in the context of the Serializer.",
                        code="request_missing",
                    )
                }
            )
        return request


class HeaderSerializerMixin(RequestFromContextMixin):

    take_from_headers: ClassVar[List[str]] = []
    """Headers to take values from.
    Header names will be converted to snake_case.
    """

    @cached_property
    def header_values(self) -> Dict[str, Any]:
        request = self.request_from_context
        return {key.replace("-", "_").lower(): request.headers.get(key, None) for key in self.take_from_headers}

    def add_headers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Remove any values added to original header names.
        for key in self.take_from_headers:
            data.pop(key, None)
        data.update(self.header_values)
        return data

    def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ret = super().to_internal_value(data)
        ret = self.add_headers(ret)
        return ret

    def to_representation(self, instance) -> Dict[str, Any]:
        ret = super().to_representation(instance)
        ret = self.add_headers(ret)
        return ret


class CookieSerializerMixin(RequestFromContextMixin):

    take_from_cookies: ClassVar[List[str]] = []
    """Cookies to take values from.
    Cookie names will be converted to snake_case.
    """

    @cached_property
    def cookie_values(self) -> Dict[str, Any]:
        request = self.request_from_context
        return {key.replace("-", "_").lower(): request.COOKIES.get(key, None) for key in self.take_from_cookies}

    def add_cookies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Remove any values added to original cookie names.
        for key in self.take_from_cookies:
            data.pop(key, None)
        data.update(self.cookie_values)
        return data

    def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ret = super().to_internal_value(data)
        ret = self.add_cookies(ret)
        return ret

    def to_representation(self, instance) -> Dict[str, Any]:
        ret = super().to_representation(instance)
        ret = self.add_cookies(ret)
        return ret


class HeaderAndCookieSerializer(HeaderSerializerMixin, CookieSerializerMixin, serializers.Serializer):
    """Serializer that adds the specified headers and cookies from request to the serializer data.
    Serializer must have the incoming request object in its context dictionary.
    If the specified header or cookie is not found in the request, the value will be None.
    """

    @cached_property
    def fields(self) -> Dict[str, serializers.Field]:
        fields = super().fields
        for header_name in self.take_from_headers:
            fields[header_name] = serializers.CharField(default=None, allow_null=True, allow_blank=True)
        for cookie_name in self.take_from_cookies:
            fields[cookie_name] = serializers.CharField(default=None, allow_null=True, allow_blank=True)
        return fields
