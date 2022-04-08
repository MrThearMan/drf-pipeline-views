# OpenAPI Schema

Pipeline views support OpenAPI schema by default, but you need to install
some optional dependencies, [as with Django REST framework][drf-schema].

```shell
pip install drf-pipeline-views[schema]
```

Here is an example pipeline.

```python
from django.urls import path
from rest_framework import serializers
from rest_framework.schemas import get_schema_view

from pipeline_views.views import BasePipelineView


class InputSerializer(serializers.Serializer):
    """Example Input"""

    name = serializers.CharField(help_text="foo")
    age = serializers.IntegerField(help_text="bar")


class OutputSerializer(serializers.Serializer):
    """Example Output"""

    email = serializers.EmailField(help_text="fizz")
    age = serializers.IntegerField(help_text="buzz")


def example_method(name: str, age: int):
    ...


class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }


urlpatterns = [
    path("example", ExampleView.as_view(), name="example"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
        ),
        name="openapi-schema",
    ),
]
```

This gets converted to the following openapi schema.

```yaml
paths:
  /example:
    post:
      operationId: createInput
      description: Example Input
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Input'
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Output'
          description: Example Output
      tags:
      - example
components:
  schemas:
    Detail:
      type: object
      properties:
        detail:
          type: string
      required:
      - detail
    Input:
      type: object
      properties:
        name:
          type: string
          description: foo
        age:
          type: integer
          description: bar
      required:
      - name
      - age
    Output:
      type: object
      properties:
        email:
          type: string
          format: email
          description: fizz
        age:
          type: integer
          description: buzz
      required:
      - email
      - age
```

## Additional responses

You can add additional responses in the initialization of the schema.
The following adds an error response as if given by raising an APIException.
It uses the "Detail" component in the OpenAPI chema, which is automatically
added for this purpose.

```python hl_lines="12 13 14 15 16"
from pipeline_views.schema import PipelineSchema


class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        responses={
            "POST": {
                404: "This is the error message"
            }
        }
    )
```

> In case your pipeline returns a list response, a default 204 response will be added automatically.

### Dynamic responses

You can also define dynamic responses with the help of MockSerializer.

```python hl_lines="13 14 15 16 17 18 19 20 21 22 23 24 25 26"
from pipeline_views.schema import PipelineSchema
from pipeline_views.serializers import MockSerializer


class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        responses={
            "POST": {
                404: MockSerializer.with_example(
                    description="This is the error message",
                    response={
                        "{date}": {
                            "{time}": [
                                "'free' or 'not free'",
                            ],
                        },
                    },
                )
            }
        }
    )
```

This adds the following response in the schema.

```yaml
paths:
  /example:
    post:
      responses:
        '404':
          content:
            application/json:
              schema:
                type: object
                properties:
                  '{date}':
                    type: object
                    properties:
                      '{time}':
                        type: array
                        items:
                          type: string
                          default: '''free'' or ''not free'''
          description: This is the error message
```

## Deprecation

You can deprecate endpoints on a method by method basis.

```python hl_lines="9"
class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        deprecated=["POST"],
    )
```

## Security

Add security schemes to the endpoints.

```python hl_lines="9 10 11 12 13 14 15"
class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        security={
            "POST": [
                {
                    "my_security": [],
                },
            ],
        },
    )
```

The security scheme also needs to be added to the SchemaGenerator class to actually work.
This can be done in `rest_framework.schemas.openapi.SchemaGenerator.get_schema`,
by adding the appropriate configuration to `schema["components"]["securitySchemes"]`.

Here is an example config for adding JWT authentication.

```python
from rest_framework.schemas.openapi import SchemaGenerator


class MySchemaGenerator(SchemaGenerator):

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema["components"]["securitySchemes"] = {
            "my_security": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
        }
```

## Query and path parameters

For pipelines using the get method, input serializer fields are interpreted automatically
as query parameters. If the endpoint has path parameters, those are used in the
schema instead, but with the documentation from the input serializer.

For other HTTP methods, you need to explicitly state that a field in the
input serializer should be given as a query parameter. This is just for schema definition,
the endpoints will actually accept the input from both places.

```python hl_lines="9 10 11"
class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        query_parameters={
            "POST": ["name"],
        },
    )
```

## External docs

External docs for an endpoint can also be added.

```python hl_lines="9 10 11 12 13 14"
class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        external_docs={
            "POST": {
                "description": "Look here for more information",
                "url": "...",
            },
        },
    )
```


[drf-schema]: https://www.django-rest-framework.org/api-guide/schemas/#install-dependencies