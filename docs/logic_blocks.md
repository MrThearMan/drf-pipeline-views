# Logic Blocks

Pipeline logic, as well as serializers, can be grouped into blocks:

```python hl_lines="5 6 7 8"
class SomeView(GetMixin, BaseAPIView):

    pipelines = {
        "GET": [
            [
                block1_step1,
                block1_step2,
            ],
            [
                SerializerBlock2,
                block2_step1,
                block2_step2,
            ],
        ],
    }
```

Logic blocks are useful if you want to skip some parts of the logic under certain conditions,
e.g., to return a cached result. This can be accomplished by raising a `NextLogicBlock` exception.
The exception can be initialized with:

1. `NextLogicBlock()`, which passes given keyword arguments to the next step in the logic (or to the response if it's
the last step in the logic) as a dictionary

2. `NextLogicBlock.with_output(output=...)`, which passes any other output like lists or strings.

```python hl_lines="5 6 13 14"
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

Logic blocks can be stacked recursively inside each other. In this case, `NextLogicBlock` will return to the
parent logic block.

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

Although `NextLogicBlock` can be used on the base level of the pipeline, this should generally be avoided,
keeping the justification for input and output serializers in mind.
