from rest_framework.request import Request
from rest_framework.response import Response

from .typing import Any, DataDict, Protocol
from .utils import translate


__all__ = [
    "GetMixin",
    "PostMixin",
    "PutMixin",
    "PatchMixin",
    "DeleteMixin",
]


class HTTPMethod(Protocol):
    def _process_request(self, data: DataDict) -> Response:
        """Process request"""


class GetMixin:
    @translate
    def get(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        kwargs.update({k: v for k, v in request.query_params.items()})
        return self._process_request(data=kwargs)


class PostMixin:
    @translate
    def post(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        kwargs.update({k: v for k, v in request.data.items()})
        kwargs.pop("csrfmiddlewaretoken", None)
        return self._process_request(data=kwargs)


class PutMixin:
    @translate
    def put(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        kwargs.update({k: v for k, v in request.data.items()})
        return self._process_request(data=kwargs)


class PatchMixin:
    @translate
    def patch(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        kwargs.update({k: v for k, v in request.data.items()})
        return self._process_request(data=kwargs)


class DeleteMixin:
    @translate
    def delete(self: HTTPMethod, request: Request, *args: Any, **kwargs: Any) -> Response:  # pylint: disable=W0613
        kwargs.update({k: v for k, v in request.data.items()})
        return self._process_request(data=kwargs)
