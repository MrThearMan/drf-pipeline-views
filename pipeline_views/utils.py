import asyncio
from contextlib import contextmanager
from functools import wraps
from itertools import chain
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.translation import get_language as current_language
from django.utils.translation import override
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None

from .typing import (
    Any,
    Callable,
    DataDict,
    Generator,
    GenericView,
    HTTPMethod,
    LogicCallable,
    Optional,
    ParamSpec,
    SerializerType,
    TypeGuard,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    from .views import BasePipelineView


__all__ = [
    "Sentinel",
    "get_language",
    "get_view_method",
    "is_pydantic_model",
    "is_serializer_class",
    "run_parallel",
    "translate",
]


T = TypeVar("T")
P = ParamSpec("P")


class Sentinel:
    """Sentinel value."""


def is_serializer_class(obj: Any) -> TypeGuard[BaseSerializer]:
    return isinstance(obj, type) and issubclass(obj, BaseSerializer)


def is_pydantic_model(obj: Any) -> bool:
    if BaseModel is None:  # pragma: no cover
        return False

    return isinstance(obj, type) and issubclass(obj, BaseModel)


def get_language(request: Request) -> str:
    """Get language based on request Accept-Language header or 'lang' query parameter."""
    lang: Optional[str] = request.query_params.get("lang")
    language_code: Optional[str] = getattr(request, "LANGUAGE_CODE", None)
    available_languages: list[str] = [key for (key, value) in settings.LANGUAGES]

    if lang and lang in available_languages:
        return lang
    if language_code and language_code in available_languages:
        return language_code

    return current_language()


def translate(item: Union[Callable[P, T], Request]) -> Union[Generator[Any, Any, None], Callable[P, T]]:
    """
    Override current language with one from language header or 'lang' parameter.
    Can be used as a context manager or a decorator. If a function is decorated,
    one of the parameters for the function must be a `rest_framework.Request` object.
    """
    if not isinstance(item, Request):

        @wraps(item)
        def decorator(*args: P.args, **kwargs: P.kwargs) -> Any:
            request = None
            for arg in chain(args, kwargs.values()):
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                msg = "No Request-object in function parameters."
                raise ValueError(msg)

            with override(get_language(request)):
                return item(*args, **kwargs)

        return decorator

    @contextmanager
    def context_manager(request: Request) -> Generator[Any, Any, None]:
        with override(get_language(request)):
            yield

    return context_manager(item)


async def run_parallel(step: tuple[Union[LogicCallable, SerializerType], ...], data: DataDict) -> tuple[DataDict, ...]:
    return await asyncio.gather(*(task(**data) for task in step))


def get_view_method(method: HTTPMethod) -> GenericView:
    source = "query_params" if method == "GET" else "data"

    def inner(
        self: "BasePipelineView",
        request: Request,
        *args: Any,  # noqa: ARG001
        **kwargs: Any,
    ) -> Response:
        kwargs.update(
            {
                key: value
                for key, value in getattr(request, source, {}).items()
                if key not in getattr(self, f"ignored_{method.lower()}_params", set())
            },
        )
        return self.process_request(data=kwargs)

    return inner
