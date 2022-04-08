# Metadata class

Pipeline views include a metadata class that adds additional data to OPTIONS responses
based on defined pipelines. For example, a pipeline defined like this:

```python
class InputSerializer(serializers.Serializer):
    """Example Input"""

    name = serializers.CharField(help_text="Help")
    age = serializers.IntegerField()


class OutputSerializer(serializers.Serializer):
    """Example Output"""

    email = serializers.EmailField(help_text="Text")
    age = serializers.IntegerField()


class ExampleView(BasePipelineView):
    """This is the description"""

    pipelines = {
        "GET": [
            InputSerializer,
            OutputSerializer,
        ],
    }

```

...will produce the following OPTIONS response:

```json
{
    "name": "Example",
    "description": "This is the description",
    "renders": [
        "application/json",
        "text/html"
    ],
    "parses": [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data"
    ],
    "actions": {
        "GET": {
            "input": {
                "name": {
                    "type": "string",
                    "required": true,
                    "help_text": "Help"
                },
                "age": {
                    "type": "integer",
                    "required": true
                }
            },
            "output": {
                "email": {
                    "type": "email",
                    "required": true,
                    "help_text": "Text"
                },
                "age": {
                    "type": "integer",
                    "required": true
                }
            }
        }
    }
}
```
