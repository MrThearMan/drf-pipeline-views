# Async Logic Callables

Pipeline logic callables can also be coroutines.
The best part about coroutines is that they can be run in parallel.
You parallel execution in a pipeline easily with a tuple, i.e., a `parallel block`.


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
from pipeline_views import BasePipelineView
from .services import async_step1, async_step2_1, async_step2_2, async_step3


class SomeView(BasePipelineView):

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

Now `async_step2_1` and `async_step2_2` will be executed in parallel, and will both receive all the
arguments from `async_step1`. `async_step2_1` and `async_step2_2` should return dictionaries like standard
pipeline logic methods. `async_step3` will then receive a union of the results of these coroutines.
If the return dictionaries of the two coroutines have any common keys, the value from the coroutine defined last
in the parallel block will be used.

Return values from the callable before the parallel excecution can be passed to the next step after the
parallel execution by setting `...` (ellipses) in the tuple. If there are any common keys in this case,
the values from the logic block will be prioritized.

```python title="views.py" hl_lines="13"
from pipeline_views import BasePipelineView
from .services import async_step1, async_step2_1, async_step2_2, async_step3


class SomeView(BasePipelineView):

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
