# Logic Blocks

Pipeline logic, as well as serializers, can be grouped into blocks:

```python hl_lines="5 6 7 8"
class SomeView(BasePipelineView):

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

These can be useful if you want to:

1. Define and reuse a logic block in multiple pipelines.
2. Separate related parts of the pipeline for clarity.
3. Skip some parts of the logic under certain conditions, e.g., to return a cached result.

Raising a `NextLogicBlock` exception within a logic block will exit the logic block with the data given to it.
`NextLogicBlock(**kwargs)`, will output the given kwargs and, `NextLogicBlock.with_output(output=...)`,
will output the given output, e.g., a list.

```python hl_lines="4 5 12 13"
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

---

Logic blocks can be stacked recursively inside each other. In this case, `NextLogicBlock` will return to the
parent logic block.

```python
class SomeView(BasePipelineView):

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
