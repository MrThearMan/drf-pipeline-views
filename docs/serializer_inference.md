# Serializer inference

### Input serializer

A pipeline can also be constructed without Serializers.

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

BaseAPIView will try to infer an input serializer with the correct serializer fields,
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

### Output serializer

Serializer inference can be extended to create output serializers a well.
In this case, the last callable would be used (`step5` in this case), and the
inference would be done based on it's output type.

For this, `BaseAPIView.get_serializer(...)` needs `output=True` in it's kwargs.
`output=True` can also be passed to `BaseAPIView.get_serializer_class(...)`.
A TypedDict (or a list containing a TypedDict) should be used so that Fields
can be determined.
