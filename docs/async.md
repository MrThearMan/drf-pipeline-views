# Async Logic Callables

Pipeline logic callables can also be coroutines.
The best part about coroutines is that they can be run in parallel.
You can configure this in the pipeline easily with a tuple.


```python title="services.py"
async def async_step1(...):
    ...


async def async_step2_1(...):
    ...


async def async_step2_2(...):
    ...


async def async_step3(...):
    ...
```

```python title="views.py" hl_lines="10 11 12 13"
from pipeline_views import BaseAPIView, GetMixin
from .services import async_step1, async_step2_1, async_step2_2, async_step3


class SomeView(GetMixin, BaseAPIView):

    pipelines = {
        "GET": [
            async_step1,
            (
                async_step2_1,
                async_step2_2,
            ),
            async_step3,
        ],
    }
```

Now `async_step2_1` and `async_step2_2` will be executed in parallel. They should return dictionaries
like standard pipeline logic methods, and then `async_step3` will receive a union of the results of these
coroutines. `async_step2_1` and `async_step2_2` will both receive all the arguments from `async_step1`.

Return values from the callable before the parallel excecution can be passed to the next step after the
parallel execution by setting "..." (ellipses) in the tuple.

```python title="views.py" hl_lines="13"
from pipeline_views import BaseAPIView, GetMixin
from .services import async_step1, async_step2_1, async_step2_2, async_step3


class SomeView(GetMixin, BaseAPIView):

    pipelines = {
        "GET": [
            async_step1,
            (
                async_step2_1,
                async_step2_2,
                ...
            ),
            async_step3,
        ],
    }
```
