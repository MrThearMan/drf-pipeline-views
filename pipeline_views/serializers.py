from django.utils.functional import cached_property
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.request import Request
from rest_framework.settings import api_settings

from .typing import Any, ClassVar, Optional

__all__ = [
    "CookieSerializerMixin",
    "HeaderAndCookieSerializer",
    "HeaderSerializerMixin",
    "RequestFromContextMixin",
]


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
                    ),
                },
            )
        return request


class HeaderSerializerMixin(RequestFromContextMixin):
    take_from_headers: ClassVar[list[str]] = []
    """Headers to take values from.
    Header names will be converted to snake_case.
    """

    @cached_property
    def header_values(self) -> dict[str, Any]:
        request = self.request_from_context
        return {key.replace("-", "_").lower(): request.headers.get(key, None) for key in self.take_from_headers}

    def add_headers(self, data: dict[str, Any]) -> dict[str, Any]:
        # Remove any values added to original header names.
        for key in self.take_from_headers:
            data.pop(key, None)
        data.update(self.header_values)
        return data

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        ret = super().to_internal_value(data)
        return self.add_headers(ret)

    def to_representation(self, instance: Any) -> dict[str, Any]:
        ret = super().to_representation(instance)
        return self.add_headers(ret)


class CookieSerializerMixin(RequestFromContextMixin):
    take_from_cookies: ClassVar[list[str]] = []
    """Cookies to take values from.
    Cookie names will be converted to snake_case.
    """

    @cached_property
    def cookie_values(self) -> dict[str, Any]:
        request = self.request_from_context
        return {key.replace("-", "_").lower(): request.COOKIES.get(key, None) for key in self.take_from_cookies}

    def add_cookies(self, data: dict[str, Any]) -> dict[str, Any]:
        # Remove any values added to original cookie names.
        for key in self.take_from_cookies:
            data.pop(key, None)
        data.update(self.cookie_values)
        return data

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        ret = super().to_internal_value(data)
        return self.add_cookies(ret)

    def to_representation(self, instance: Any) -> dict[str, Any]:
        ret = super().to_representation(instance)
        return self.add_cookies(ret)


class HeaderAndCookieSerializer(HeaderSerializerMixin, CookieSerializerMixin, serializers.Serializer):
    """
    Serializer that adds the specified headers and cookies from request to the serializer data.
    Serializer must have the incoming request object in its context dictionary.
    If the specified header or cookie is not found in the request, the value will be None.
    """

    @cached_property
    def fields(self) -> dict[str, serializers.Field]:
        fields = super().fields
        for header_name in self.take_from_headers:
            fields[header_name] = serializers.CharField(default=None, allow_null=True, allow_blank=True)
        for cookie_name in self.take_from_cookies:
            fields[cookie_name] = serializers.CharField(default=None, allow_null=True, allow_blank=True)
        return fields
