# Conditional logic paths

Sometimes you might want to run different logic based on the output from the previous logic method.
This can be accomplished with conditional logic paths.

```python hl_lines="13 14 15 16"
def step1(data):
    if condition:
        return "foo", data
    else:
        return "bar", data


class SomeView(BasePipelineView):

    pipelines = {
        "GET": [
            step1,
            {
                "foo": step2_1,
                "bar": step2_2,
            },
            ...
        ],
    }
```

Notice that `step1` returned a tuple of the data and key used to select the logic in the next step.
Data should still be a dict, which matches what ever logic the key selects from the next step.
Conditional paths also work inside logic blocks.

You could also use conditionals to run only one method from a logic block, since it just uses
`__getitem__` to select the next logic method.

```python hl_lines="13 14 15 16"
def step1(data):
    if condition:
        return 0, data
    else:
        return 1, data


class SomeView(BasePipelineView):

    pipelines = {
        "GET": [
            step1,
            [
                block1_step1,  # run if condition is truthy
                block1_step2,  # run if condition is falsy
            ],
            ...
        ],
    }
```