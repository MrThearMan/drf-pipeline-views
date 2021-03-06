# OpenAPI Schema

Pipeline views support OpenAPI schema by default, but you need to install
some optional dependencies, [as with Django REST framework][drf-schema].

```shell
pip install drf-pipeline-views[schema]
# Or add `drf-pipeline-views[schema]` to `requirements.txt`.
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
    return {"email": f"{name.lower()}@email.com", "age": age}


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

This gets converted to the following OpenAPI schema.

```yaml title="openapi"
openapi: 3.0.2
info:
  title: Your Project
  version: 1.0.0
  description: API for all things
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
          application/x-www-form-urlencoded:
            schema:
              $ref: '#/components/schemas/Input'
          multipart/form-data:
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

The library also includes an optional `PipelineSchemaGenerator` which can be used
to help create a versioned API while maintaining appropriate tags,
and add additional information to the API. This will also sort the tags
and the endpoints under those tags alphabetically.

```python hl_lines="1 11 12 13 14 15 16"
from pipeline_views.schema import PipelineSchemaGenerator

urlpatterns = [
    path("api/v1/example/", ExampleView.as_view(), name="test_view"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
            url="api/v1/",
            generator_class=PipelineSchemaGenerator.configure(
                contact={"email": "user@example.com"},
                license={"name": "MIT"},
                terms_of_service="example.com",
            ),
        ),
        name="openapi-schema",
    ),
]
```
```yaml title="openapi" hl_lines="6 7 8 9 10 12 15 16"
openapi: 3.0.2
info:
  title: Your Project
  version: 1.0.0
  description: API for all things
  contact:
    email: user@example.com
  license:
    name: MIT
  termsOfService: example.com
paths:
  /api/v1/example/:
    post:
      # ...
      tags:
      - example
# ...
```


## Additional responses

You can add additional responses in the initialization of the schema.

```python hl_lines="5 6 7 8 9 10 21 22 23 24 25 26"
from rest_framework import serializers
from pipeline_views.schema import PipelineSchema


class ErrorSerializer(serializers.Serializer):
    """This is a custom error"""

    loc = serializers.ListField(child=serializers.CharField())
    msg = serializers.CharField()
    type = serializers.CharField()


class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        responses={
            "POST": {
                400: ErrorSerializer,
                404: "This is the error message"
            }
        }
    )
```
```yaml title="openapi" hl_lines="8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41"
# ...
paths:
  /example/:
    post:
      # ...
      responses:
        # ...
        '400':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
          description: This is a custom error
        '404':
          content:
            application/json:
              schema:
                type: object
                properties:
                  detail:
                    type: string
                    default: error message
          description: This is the error message
components:
  schemas:
    # ...
    Error:
      type: object
      properties:
        loc:
          type: array
          items:
            type: string
        msg:
          type: string
        type:
          type: string
      required:
      - loc
      - msg
      - type
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
```yaml title="openapi" hl_lines="8 9 10 11 12 13 14 15 16 17 18 19 20 21 22"
# ...
paths:
  /example:
    post:
      # ...
      responses:
        # ...
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
# ...
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

## Security schemes

Add security schemes to the endpoints.

```python hl_lines="9 10 11 12 13"
class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        security={
            "POST": {
                "my_security": [],
            },
        },
    )
```

> The value for the security scheme defines its [scopes].

The security scheme also needs to be added to the SchemaGenerator class to actually work.
This can be done in `rest_framework.schemas.openapi.SchemaGenerator.get_schema`,
by adding the appropriate configuration to `schema["components"]["securitySchemes"]`.
`PipelineSchemaGenerator` can do this for you.

```python hl_lines="11 12 13 14 15 16 17 18 19"
from pipeline_views.schema import PipelineSchemaGenerator

urlpatterns = [
    path("example/", ExampleView.as_view(), name="test_view"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
            generator_class=PipelineSchemaGenerator.configure(
                security_schemes={
                    "my_security": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    },
                },
            ),
        ),
        name="openapi-schema",
    ),
]
```
```yaml title="openapi" hl_lines="4 5 6 7 8"
# ...
components:
  # ...
  securitySchemes:
    my_security:
      type: http
      scheme: bearer
      bearerFormat: JWT
# ...
```

### Automatic security schemes

You can also define rules that will automatically add certain security schemes
to views based on their authentication and permission classes. The key for the
security rules is either a single authentication and permission class, or a
tuple of them. If the view already has any of the schemas defined for it,
the view's configuration will take precedence.

```python hl_lines="7 29 30 31 32 33"
from rest_framework.permissions import IsAuthenticated
from pipeline_views.schema import PipelineSchemaGenerator

class ExampleView(BasePipelineView):
    """Example View"""

    permission_classes = [IsAuthenticated]

    pipelines = {
        "POST": [...],
    }

urlpatterns = [
    path("example/", ExampleView.as_view(), name="test_view"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
            generator_class=PipelineSchemaGenerator.configure(
                security_schemes={
                    "my_security": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    },
                },
                security_rules={
                    IsAuthenticated: {
                        "my_security": [],
                    },
                },
            ),
        ),
        name="openapi-schema",
    ),
]
```
```yaml title="openapi" hl_lines="6 7"
# ...
paths:
  /example:
    post:
      # ...
      security:
      - my_security: []
components:
  # ...
  securitySchemes:
    my_security:
      type: http
      scheme: bearer
      bearerFormat: JWT
# ...
```

## Query and path parameters

For pipelines using the GET method, input serializer fields are interpreted automatically
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

## Public

Endpoints can be set public/private for the whole API (public by default).
Private endpoints are not visible to users that do not have the appropriate
permissions.

```python hl_lines="11 12 13"
from pipeline_views.schema import PipelineSchemaGenerator

urlpatterns = [
    path("example/", ExampleView.as_view(), name="test_view"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
            generator_class=PipelineSchemaGenerator.configure(
                public=False,
            ),
        ),
        name="openapi-schema",
    ),
]
```

You can also set individual endpoints public/private. This will override
the API-wide configuration.

```python hl_lines="9 10 11"
class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [...],
    }

    schema = PipelineSchema(
        public={
            "POST": False,
        },
    )
```


[drf-schema]: https://www.django-rest-framework.org/api-guide/schemas/#install-dependencies
[scopes]: https://swagger.io/docs/specification/authentication/#scopes
