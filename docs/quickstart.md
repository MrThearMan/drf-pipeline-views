# Basic Usage

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

def step4(step4_input1, step4_input2, **kwargs):  # Ignore other inputs with kwargs
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
            step1,
            step2,
            step3,
            step4,
            step5,
            OutputSerializer,
        ],
    }
```

Using input and output serializers like this forces verification of the incoming and outcoming data,
so that if something changes in the logic, or some unexpected values are returned,
the endpoint will break instead of creating side effects in the application using the API.
