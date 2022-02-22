from django.utils.translation import get_language
from rest_framework.request import Request
from rest_framework.response import Response

from .typing import Any, DataDict, Optional, Protocol, Set
from .utils import translate


__all__ = [
    "GetMixin",
    "PostMixin",
    "PutMixin",
    "PatchMixin",
    "DeleteMixin",
]


class HTTPMethod(Protocol):
    ignored_get_params: Set[str]
    ignored_post_params: Set[str]
    ignored_put_params: Set[str]
    ignored_patch_params: Set[str]
    ignored_delete_params: Set[str]

    def process_request(self, data: DataDict, lang: Optional[str] = None) -> Response:
        """Process request"""


class GetMixin:
    """Mixin for implementing GET request for an endpoint."""

    ignored_get_params = {"lang", "format"}

    @translate
    def get(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        params = {k: v for k, v in request.query_params.items() if k not in self.ignored_get_params}
        kwargs.update(params)
        return self.process_request(data=kwargs, lang=get_language())


class PostMixin:
    """Mixin for implementing POST request for an endpoint."""

    ignored_post_params = {"csrfmiddlewaretoken", "lang", "format"}

    @translate
    def post(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        params = {k: v for k, v in request.data.items() if k not in self.ignored_post_params}
        kwargs.update(params)
        return self.process_request(data=kwargs, lang=get_language())


class PutMixin:
    """Mixin for implementing PUT request for an endpoint."""

    ignored_put_params = {"lang", "format"}

    @translate
    def put(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        params = {k: v for k, v in request.data.items() if k not in self.ignored_put_params}
        kwargs.update(params)
        return self.process_request(data=kwargs, lang=get_language())


class PatchMixin:
    """Mixin for implementing PATCH request for an endpoint."""

    ignored_patch_params = {"lang", "format"}

    @translate
    def patch(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        params = {k: v for k, v in request.data.items() if k not in self.ignored_patch_params}
        kwargs.update(params)
        return self.process_request(data=kwargs, lang=get_language())


class DeleteMixin:
    """Mixin for implementing DELETE request for an endpoint."""

    ignored_delete_params = {"lang", "format"}

    @translate
    def delete(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        params = {k: v for k, v in request.data.items() if k not in self.ignored_delete_params}
        kwargs.update(params)
        return self.process_request(data=kwargs, lang=get_language())
