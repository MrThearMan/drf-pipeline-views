# Quickstart

##  Basic Usage

Let's create a basic pipeline:

```python
def step1(step1_input1, step1_input2):
    # Process the data to different form
    return {"step3_input1": ..., "step3_input2": ...}

def step2(**kwargs):
    # Run validation without touching the data
    return kwargs

def step3(step3_input1, step3_input2):  # Matches return from step 1
    # Maybe do some database or API calls here
    # to isolate it from the rest of the rest of the logic
    return {"step4_input1": ..., "step4_input2": ..., "step4_input3": ...}

def step4(step4_input1, step4_input2, **kwargs):  # Ignore other inputs
    # Process the data, but do not return anything -> next step takes no input
    return

def step5():
    # Build some response
    return {"end_result1": ..., "end_result2": ...}
```

Next, we'll create input and output serializers for our endpoint:

```python
from rest_framework import fields
from rest_framework.serializers import Serializer

class InputSerializer(Serializer):
    step1_input1 = fields.CharField()
    step1_input2 = fields.DateField()

class OutputSerializer(Serializer):
    end_result1 = fields.CharField()
    end_result2 = fields.FloatField()
```

Finally, we can create our view:

```python
from pipeline_views import BaseAPIView, GetMixin


class SomeView(GetMixin, BaseAPIView):

  pipelines = {
    "GET": [
        InputSerializer,
        [
            step1,
            step2,
            step3,
            step4,
            step5,
        ],
        OutputSerializer,
    ],
  }
```

Using input and output serializers like this forces verification of the incoming and outcoming data,
so that if something changes in the logic, or some unexpected values are returned,
the endpoint will break instead of creating side effects in the application using the API.

## Serializer inference

Using serializers is totally optional. A pipeline like this will work just as well:

```python
class SomeView(GetMixin, BaseAPIView):

  pipelines = {
    "GET": [
        step1,
        step2,
        step3,
        step4,
        step5,
    ],
  }
```

BaseAPIView will try to infer a serializer with the correct serializer fields for
based on the type hints to the first function `step1`.

```python
from rest_framework.fields import CharField, IntegerField
from pipeline_views import MockSerializer

# Callable
def logic_callable(name: str, age: int):
    ...

# Inferred Serializer
class LogicCallableSerializer(MockSerializer):
    name = CharField()
    age = IntegerField()
```

This is only used by the Django REST Framework Browsable API to create forms.
`MockSerializer` makes sure the fields are only used for input and not validation.

## Logic Blocks

Pipeline logic can be grouped into blocks:

```python
class SomeView(GetMixin, BaseAPIView):

  pipelines = {
    "GET": [
        [
            block1_step1,
            block1_step2,
        ],
        [
            block2_step1,
            block2_step2,
        ],
    ],
  }
```

Logic blocks are useful if you want to skip some logic methods under certain conditions, e.g., to return a cached result.
This can be accomplished by raising a `NextLogicBlock` exception. The exception can be initialized with:
1. `NextLogicBlock()`, which passes given keyword arguments to the next step in the logic (or to the response if it's
the last step in the logic) as a dictionary
2. `NextLogicBlock.with_output(output=...)`, which passes any other output like lists or strings.

```python
from pipeline_views import NextLogicBlock


def block1_step1(step1_input1, step1_input2):
    if condition:
        raise NextLogicBlock(step3_input1=..., step3_input2=...)
    ...

def block1_step2(step2_input1, step2_input2):
    ...

def block2_step1(step3_input1, step3_input2):
    if condition:
        raise NextLogicBlock.with_output(output=...)
    ...

def block2_step2():
    ...
```

Logic blocks can be stacked recursively inside each other. In this case, `NextLogicBlock` will return to the parent logic block.

```python
class SomeView(GetMixin, BaseAPIView):

  pipelines = {
    "GET": [
        [
            block1_step1,
            [
                block2_step1,
                [
                    block3_step1,
                    [
                        ...
                    ],
                ],
            ],
        ],
    ],
  }
```

> Note that `NextLogicBlock` does not work on the base level of the pipeline! The base level of the pipeline should be treated
> as mandatory for the endpoint, keeping the justification for input and output serializers in mind.
> If you need to escape all of you logic, you can simply put it to a single block on the base level and rely on inferred serializers.
> You might also consider raising exceptions from rest_framework.exceptions (or maybe even your own) to interrupt the path logic completely.

## Modifying endpoint data

If you wish to add data to a request, you can do that on the endpoint level by overriding
`_process_request`, or on the endpoint HTTP method level by overriding the spesific method, like `get`.

```python
from rest_framework.exceptions import NotAuthenticated
from rest_framework.authentication import get_authorization_header
from pipeline_views import BaseAPIView, GetMixin


class BasicView(GetMixin, BaseAPIView):

    pipelines = {"GET": ...}

    def get(self, request, *args, **kwargs):
        # Add language to every get request for this endpoint
        kwargs["lang"] = request.LANGUAGE_CODE
        return super().get(request, *args, **kwargs)

    def _process_request(self, data):
        # Add authorization token to every http method
        data["token"] = self._token_from_headers()
        return super()._process_request(data)

    def _token_from_headers(self):
        auth_header = get_authorization_header(self.request)
        if not auth_header:
            raise NotAuthenticated("You must be logged in for this endpoint.")
        return auth_header.split()[1].decode()
```
