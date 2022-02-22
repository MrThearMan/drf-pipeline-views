import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import wraps
from itertools import chain

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import get_language as current_language
from django.utils.translation import override
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from .typing import (
    Any,
    Callable,
    DataDict,
    Generator,
    List,
    LogicCallable,
    Optional,
    P,
    SerializerType,
    T,
    Tuple,
    Union,
)


__all__ = [
    "sentinel",
    "get_language",
    "translate",
    "is_serializer_class",
    "cache_pipeline_logic",
    "run_in_thread",
    "run_parallel",
]


class sentinel:  # pylint: disable=C0103
    """Sentinel value."""


available_languages: List[str] = [key for (key, value) in settings.LANGUAGES]


def is_serializer_class(obj: Any) -> bool:
    return isinstance(obj, type) and issubclass(obj, BaseSerializer)


def get_language(request: Request) -> str:
    """Get language based on request Accept-Language header or 'lang' query parameter."""
    lang: Optional[str] = request.query_params.get("lang")
    language_code: Optional[str] = getattr(request, "LANGUAGE_CODE", None)

    if lang and lang in available_languages:
        return lang
    if language_code and language_code in available_languages:
        return language_code

    return current_language()


def translate(item: Union[Callable[P, T], Request]) -> Union[Generator[Any, Any, None], Callable[P, T]]:
    """Override current language with one from language header or 'lang' parameter.
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
                raise ValueError("No Request-object in function parameters.")

            with override(get_language(request)):
                return item(*args, **kwargs)  # type: ignore

        return decorator

    @contextmanager
    def context_manager(request: Request) -> Generator[Any, Any, None]:
        with override(get_language(request)):
            yield

    return context_manager(item)


def cache_pipeline_logic(cache_key: str, timeout: int) -> Callable[P, T]:
    """Cache the result of a pipeline logic function. Calls with different arguments will be saved under
    different keys, using the given key as a prefix and joining it with a hash of the arguments.

    :param cache_key: Key to save the result under.
    :param timeout: How long to cache the data in seconds.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal cache_key
            key = cache_key + str(hash(args + tuple(kwargs.values())))
            data = run_in_thread(cache.get)(key, None)
            if data is None:
                data = await func(*args, **kwargs)
                run_in_thread(cache.set)(key, data, timeout)
            return data

        return wrapper

    return decorator


def run_in_thread(task: Callable[P, T]) -> Callable[P, T]:
    """Decorator to run given callable in a thread.
    Useful for running functions that require a database or otherwise
    cannot run in async mode.
    """

    @wraps(task)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        def func() -> T:
            return task(*args, **kwargs)

        with ThreadPoolExecutor() as executor:
            future = executor.submit(func)
            return future.result()

    return wrapper


async def run_parallel(step: Tuple[Union[LogicCallable, SerializerType], ...], data: DataDict) -> Tuple[DataDict, ...]:
    return await asyncio.gather(*[task(**data) for task in step])  # noqa
