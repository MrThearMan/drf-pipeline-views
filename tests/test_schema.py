from django.contrib.auth.models import AnonymousUser
from rest_framework.fields import CharField, IntegerField
from rest_framework.reverse import reverse
from rest_framework.serializers import Serializer
from rest_framework.test import APIClient

from pipeline_views import BasePipelineView, MockSerializer
from pipeline_views.schema import PipelineSchema, PipelineSchemaGenerator
from pipeline_views.serializers import EmptySerializer, HeaderAndCookieSerializer
from tests.django.urls import (
    ExamplePathView,
    ExampleView,
    InputSerializer,
    OutputSerializer,
    PydanticInput,
    PydanticOutput,
    example_method,
)


def test_pipeline_schema__get_components(drf_request):
    class CustomView(ExampleView):
        """Custom View"""

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    components = view.schema.get_components()
    assert components == {
        "Input": {
            "properties": {
                "age": {
                    "type": "integer",
                },
                "name": {
                    "type": "string",
                },
            },
            "required": ["name", "age"],
            "type": "object",
        },
        "Output": {
            "properties": {
                "age": {
                    "type": "integer",
                },
                "email": {
                    "format": "email",
                    "type": "string",
                },
            },
            "required": ["email", "age"],
            "type": "object",
        },
    }


def test_pipeline_schema__get_webhook(drf_request):
    schema = PipelineSchemaGenerator(
        root_url="api",
        webhooks={
            "Example": {
                "method": "POST",
                "request_data": InputSerializer,
                "responses": {
                    200: OutputSerializer,
                    400: "Other Output",
                },
            }
        },
    )

    webhook = schema.get_webhook()
    assert webhook == {
        "Example": {
            "POST": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {
                                    "age": {
                                        "type": "integer",
                                    },
                                    "name": {
                                        "type": "string",
                                    },
                                },
                                "required": ["name", "age"],
                                "type": "object",
                            }
                        }
                    },
                    "description": "Example Input",
                },
                "responses": {
                    "200": {
                        "description": "Example Output",
                        "content": {
                            "application/json": {
                                "properties": {
                                    "age": {
                                        "type": "integer",
                                    },
                                    "email": {
                                        "format": "email",
                                        "type": "string",
                                    },
                                },
                                "required": ["email", "age"],
                                "type": "object",
                            }
                        },
                    },
                    "400": {
                        "description": "Other Output",
                    },
                },
            },
        }
    }


def test_pipeline_schema__get_responses(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Output",
                    },
                },
            },
            "description": "Example Output",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
    }


def test_pipeline_schema__get_components__from_schema(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: "Unavailable",
                    404: CustomSerializer,
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    components = view.schema.get_components()
    assert components == {
        "Custom": {
            "properties": {
                "data": {
                    "type": "string",
                },
            },
            "required": ["data"],
            "type": "object",
        },
        "Input": {
            "properties": {
                "age": {
                    "type": "integer",
                },
                "name": {
                    "type": "string",
                },
            },
            "required": ["name", "age"],
            "type": "object",
        },
        "Output": {
            "properties": {
                "age": {
                    "type": "integer",
                },
                "email": {
                    "format": "email",
                    "type": "string",
                },
            },
            "required": ["email", "age"],
            "type": "object",
        },
    }


def test_pipeline_schema__get_components__list(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField()

    class ExampleSerializer(Serializer):
        """This is the description for this one"""

        many = True

        data = IntegerField()

    class CustomView(ExampleView):
        """Custom View"""

        pipelines = {
            "POST": [
                ExampleSerializer,
            ],
        }

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: "Unavailable",
                    404: CustomSerializer,
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    components = view.schema.get_components()
    assert components == {
        "Custom": {
            "items": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                    },
                },
                "required": ["data"],
            },
            "type": "array",
        },
        "Example": {
            "items": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "integer",
                    },
                },
                "required": ["data"],
            },
            "type": "array",
        },
    }


def test_pipeline_schema__get_components__union(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: ["Unavailable", CustomSerializer],
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    components = view.schema.get_components()
    assert components == {
        "Custom": {
            "properties": {
                "data": {
                    "type": "string",
                },
            },
            "required": ["data"],
            "type": "object",
        },
        "Input": {
            "properties": {
                "age": {
                    "type": "integer",
                },
                "name": {
                    "type": "string",
                },
            },
            "required": ["name", "age"],
            "type": "object",
        },
        "Output": {
            "properties": {
                "age": {
                    "type": "integer",
                },
                "email": {
                    "format": "email",
                    "type": "string",
                },
            },
            "required": ["email", "age"],
            "type": "object",
        },
    }


def test_pipeline_schema__get_responses__from_schema(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: "Unavailable",
                    404: CustomSerializer,
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Output",
                    },
                },
            },
            "description": "Example Output",
        },
        "400": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unavailable",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
        "404": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Custom",
                    },
                },
            },
            "description": "This is the description",
        },
    }


def test_pipeline_schema__get_responses__none(drf_request):
    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Output",
                    },
                },
            },
            "description": "Example Output",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
    }


def test_pipeline_schema__get_responses__union(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: ["Unavailable", CustomSerializer],
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Output",
                    },
                },
            },
            "description": "Example Output",
        },
        "400": {
            "content": {
                "application/json": {
                    "schema": {
                        "anyOf": [
                            {
                                "properties": {
                                    "detail": {
                                        "default": "error message",
                                        "type": "string",
                                    },
                                },
                                "type": "object",
                            },
                            {
                                "$ref": "#/components/schemas/Custom",
                            },
                        ],
                    },
                },
            },
            "description": "",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
    }


def test_pipeline_schema__get_responses__wrong_method(drf_request):
    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("GET")
    assert responses == {}


def test_pipeline_schema__get_responses__list(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: "Unavailable",
                    404: CustomSerializer,
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Output",
                    },
                },
            },
            "description": "Example Output",
        },
        "400": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unavailable",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
        "404": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Custom",
                    },
                },
            },
            "description": "This is the description",
        },
    }


def test_pipeline_schema__get_responses__mock_serializer(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                MockSerializer.with_example(
                    description="This is the response",
                    response={"foo": {"bar": ["baz"]}},
                ),
            ]
        }

        schema = PipelineSchema(
            responses={
                "POST": {
                    200: ...,
                    400: "Unavailable",
                    404: CustomSerializer,
                },
            }
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "foo": {
                                "properties": {
                                    "bar": {
                                        "items": {
                                            "default": "baz",
                                            "type": "string",
                                        },
                                        "type": "array",
                                    },
                                },
                                "type": "object",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "This is the response",
        },
        "400": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unavailable",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
        "404": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Custom",
                    },
                },
            },
            "description": "This is the description",
        },
    }


def test_pipeline_schema__get_responses__add_204_if_output_is_list(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField()

    class CustomView(ExampleView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                CustomSerializer,
            ]
        }

        schema = PipelineSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Custom",
                    },
                },
            },
            "description": "This is the description",
        },
        "204": {
            "content": {
                "application/json": {
                    "default": "",
                    "type": "string",
                },
            },
            "description": "no results",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
    }


def test_pipeline_schema__get_responses__204_if_output_is_emptyserializer(drf_request):
    class CustomSerializer(EmptySerializer):
        """This is the description"""

    class CustomView(ExampleView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                CustomSerializer,
            ]
        }

        schema = PipelineSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("POST")
    assert responses == {
        "204": {
            "content": {
                "application/json": {
                    "content": {
                        "application/json": {
                            "default": "",
                            "type": "string",
                        },
                    },
                    "description": "no results",
                },
            },
            "description": "This is the description",
        },
        "401": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "detail": {
                                "default": "error message",
                                "type": "string",
                            },
                        },
                        "type": "object",
                    },
                },
            },
            "description": "Unauthenticated.",
        },
    }


def test_pipeline_schema__get_operation(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomView(ExamplePathView):
        """Custom View"""

        schema = PipelineSchema(
            responses={
                "PATCH": {
                    200: ...,
                    400: "Unavailable",
                    404: CustomSerializer,
                },
            },
            links={
                "PATCH": {
                    200: {
                        "Title": {
                            "description": "Description",
                            "operationId": "createInput",
                            "parameters": {
                                "age": "$request.body#/age",
                            },
                        },
                    },
                },
            },
            deprecated=["PATCH"],
            security={
                "PATCH": {"foo": ["bar"]},
            },
            external_docs={
                "PATCH": {"description": "foo", "url": "bar"},
            },
            query_parameters={
                "PATCH": ["name"],
            },
            callbacks={
                "event_name": {
                    "callback_url": {
                        "POST": {
                            "request_body": InputSerializer,
                            "responses": {
                                200: OutputSerializer,
                            },
                        },
                        "PUT": {
                            "request_body": PydanticInput,
                            "responses": {
                                200: PydanticOutput,
                            },
                        },
                    },
                },
            },
            operation_id_base="BaseOpId",
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "PATCH"
    view.format_kwarg = None
    operation = view.schema.get_operation("", "PATCH")
    assert operation == {
        "deprecated": True,
        "description": "Example Input",
        "externalDocs": {
            "description": "foo",
            "url": "bar",
        },
        "operationId": "partialUpdateBaseOpId",
        "parameters": [
            {
                "description": "",
                "in": "query",
                "name": "name",
                "required": True,
                "schema": {
                    "type": "string",
                },
            },
        ],
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "properties": {
                            "age": {
                                "type": "integer",
                            },
                        },
                        "required": ["age"],
                        "type": "object",
                    },
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "properties": {
                            "age": {
                                "type": "integer",
                            },
                        },
                        "required": ["age"],
                        "type": "object",
                    },
                },
                "multipart/form-data": {
                    "schema": {
                        "properties": {
                            "age": {
                                "type": "integer",
                            },
                        },
                        "required": ["age"],
                        "type": "object",
                    },
                },
            },
        },
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Output",
                        },
                    },
                },
                "description": "Example Output",
                "links": {
                    "Title": {
                        "description": "Description",
                        "operationId": "createInput",
                        "parameters": {
                            "age": "$request.body#/age",
                        },
                    },
                },
            },
            "400": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "detail": {
                                    "default": "error message",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                    },
                },
                "description": "Unavailable",
            },
            "401": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "detail": {
                                    "default": "error message",
                                    "type": "string",
                                },
                            },
                            "type": "object",
                        },
                    },
                },
                "description": "Unauthenticated.",
            },
            "404": {
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Custom",
                        },
                    },
                },
                "description": "This is the description",
            },
        },
        "security": [
            {
                "foo": ["bar"],
            },
        ],
        "tags": [""],
        "callbacks": {
            "event_name": {
                "callback_url": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "age": {
                                                "type": "integer",
                                            },
                                            "name": {
                                                "type": "string",
                                            },
                                        },
                                        "required": ["name", "age"],
                                        "type": "object",
                                    }
                                }
                            }
                        },
                        "responses": {
                            200: {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "age": {
                                                    "type": "integer",
                                                },
                                                "email": {
                                                    "format": "email",
                                                    "type": "string",
                                                },
                                            },
                                            "required": ["email", "age"],
                                            "type": "object",
                                        }
                                    }
                                }
                            }
                        },
                    },
                    "put": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "age": {
                                                "type": "integer",
                                            },
                                            "name": {
                                                "type": "string",
                                            },
                                        },
                                        "required": ["name", "age"],
                                        "type": "object",
                                    }
                                }
                            }
                        },
                        "responses": {
                            200: {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "properties": {
                                                "age": {
                                                    "type": "integer",
                                                },
                                                "email": {
                                                    "type": "string",
                                                },
                                            },
                                            "required": ["email", "age"],
                                            "type": "object",
                                        }
                                    }
                                }
                            }
                        },
                    },
                }
            }
        },
    }


def test_pipeline_schema__get_parameters__query(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            query_parameters={
                "POST": ["name", "age"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "query",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
        {
            "description": "",
            "in": "query",
            "name": "age",
            "required": True,
            "schema": {
                "type": "integer",
            },
        },
    ]


def test_pipeline_schema__get_parameters__query__not_defined(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "PUT": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomView()
    view.request = drf_request
    view.request.method = "PUT"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "PUT")
    assert parameters == []


def test_pipeline_schema__get_parameters__query__default_for_get(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "GET": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomView()
    view.request = drf_request
    view.request.method = "GET"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "GET")
    assert parameters == [
        {
            "description": "",
            "in": "query",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
        {
            "description": "",
            "in": "query",
            "name": "age",
            "required": True,
            "schema": {
                "type": "integer",
            },
        },
    ]


def test_pipeline_schema__get_parameters__query__partial(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "PUT": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            query_parameters={
                "PUT": ["name"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "PUT"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "PUT")
    assert parameters == [
        {
            "description": "",
            "in": "query",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_schema__get__parameters__query__list(drf_request):
    class CustomSerializer(InputSerializer):
        many = True

    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            query_parameters={
                "POST": ["name", "age"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "query",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
        {
            "description": "",
            "in": "query",
            "name": "age",
            "required": True,
            "schema": {
                "type": "integer",
            },
        },
    ]


def test_pipeline_scheme__get_parameters__path(drf_request):
    view = ExamplePathView()
    view.request = drf_request
    view.request.method = "PATCH"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("/{age}", "PATCH")
    assert parameters == [
        {
            "description": "",
            "in": "path",
            "name": "age",
            "required": True,
            "schema": {
                "type": "integer",
            },
        },
    ]


def test_pipeline_scheme__get_parameters__path__partial(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField(help_text="This is the data")
        name = CharField(help_text="This is the name")

    class CustomPathView(ExamplePathView):
        """Custom View"""

        pipelines = {
            "PATCH": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomPathView()
    view.request = drf_request
    view.request.method = "PATCH"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("/{data}", "PATCH")
    assert parameters == [
        {
            "description": "This is the data",
            "in": "path",
            "name": "data",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_scheme__get_parameters__path__list(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField(help_text="This is the data")

    class CustomPathView(ExamplePathView):
        """Custom View"""

        pipelines = {
            "PATCH": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomPathView()
    view.request = drf_request
    view.request.method = "PATCH"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("/{data}", "PATCH")
    assert parameters == [
        {
            "description": "This is the data",
            "in": "path",
            "name": "data",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_schema__get_parameters__header(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            header_parameters={
                "POST": ["name", "age"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "header",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
        {
            "description": "",
            "in": "header",
            "name": "age",
            "required": True,
            "schema": {
                "type": "integer",
            },
        },
    ]


def test_pipeline_schema__get_parameters__header__partial(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            header_parameters={
                "POST": ["name"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "header",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_scheme__get_parameters__header__list(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField(help_text="This is the data")

    class CustomPathView(ExamplePathView):
        """Custom View"""

        pipelines = {
            "PATCH": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            header_parameters={
                "PATCH": ["data"],
            },
        )

    view = CustomPathView()
    view.request = drf_request
    view.request.method = "PATCH"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "PATCH")
    assert parameters == [
        {
            "description": "This is the data",
            "in": "header",
            "name": "data",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_schema__get_parameters__header__special_serializer(drf_request):
    class CustomSerializer(HeaderAndCookieSerializer):
        """This is the description"""

        take_from_headers = ["name"]

        data = CharField(help_text="This is the data")

    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "header",
            "name": "name",
            "required": False,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_schema__get_parameters__cookie(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            cookie_parameters={
                "POST": ["name", "age"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "cookie",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
        {
            "description": "",
            "in": "cookie",
            "name": "age",
            "required": True,
            "schema": {
                "type": "integer",
            },
        },
    ]


def test_pipeline_schema__get_parameters__cookie__partial(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            cookie_parameters={
                "POST": ["name"],
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "cookie",
            "name": "name",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_scheme__get_parameters__cookie__list(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        many = True

        data = CharField(help_text="This is the data")

    class CustomPathView(ExamplePathView):
        """Custom View"""

        pipelines = {
            "PATCH": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            cookie_parameters={
                "PATCH": ["data"],
            },
        )

    view = CustomPathView()
    view.request = drf_request
    view.request.method = "PATCH"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "PATCH")
    assert parameters == [
        {
            "description": "This is the data",
            "in": "cookie",
            "name": "data",
            "required": True,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_schema__get_parameters__cookie__special_serializer(drf_request):
    class CustomSerializer(HeaderAndCookieSerializer):
        """This is the description"""

        take_from_cookies = ["name"]

        data = CharField(help_text="This is the data")

    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "POST": [
                CustomSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    parameters = view.schema.get_parameters("", "POST")
    assert parameters == [
        {
            "description": "",
            "in": "cookie",
            "name": "name",
            "required": False,
            "schema": {
                "type": "string",
            },
        },
    ]


def test_pipeline_schema__get_request_body(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    request_body = view.schema.get_request_body("", "POST")
    assert request_body == {
        "content": {
            "application/json": {
                "schema": {
                    "$ref": "#/components/schemas/Input",
                },
            },
            "application/x-www-form-urlencoded": {
                "schema": {
                    "$ref": "#/components/schemas/Input",
                },
            },
            "multipart/form-data": {
                "schema": {
                    "$ref": "#/components/schemas/Input",
                },
            },
        },
    }


def test_pipeline_schema__get_request_body__get(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "GET": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

    view = CustomView()
    view.request = drf_request
    view.request.method = "GET"
    view.format_kwarg = None
    request_body = view.schema.get_request_body("", "GET")
    assert request_body is None


def test_pipeline_schema__get_request_body__query_parameters(drf_request):
    class CustomView(BasePipelineView):
        """Custom View"""

        pipelines = {
            "PUT": [
                InputSerializer,
                example_method,
                OutputSerializer,
            ],
        }

        schema = PipelineSchema(
            query_parameters={"PUT": ["name"]},
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "PUT"
    view.format_kwarg = None
    request_body = view.schema.get_request_body("", "PUT")
    assert request_body == {
        "content": {
            "application/json": {
                "schema": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                    },
                    "required": ["age"],
                    "type": "object",
                },
            },
            "application/x-www-form-urlencoded": {
                "schema": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                    },
                    "required": ["age"],
                    "type": "object",
                },
            },
            "multipart/form-data": {
                "schema": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                    },
                    "required": ["age"],
                    "type": "object",
                },
            },
        },
    }


def test_pipeline_schema__get_tags(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.format_kwarg = None
    tags = view.schema.get_tags("foo/")
    assert tags == ["foo"]


def test_pipeline_schema__get_tags__predefined(drf_request):
    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema(tags=["foo", "bar"])

    view = CustomView()
    view.request = drf_request
    view.format_kwarg = None
    tags = view.schema.get_tags("")
    assert tags == ["foo", "bar"]


def test_pipeline_schema__openapi():
    client = APIClient()

    class MockUser(AnonymousUser):
        @property
        def is_authenticated(self):
            return True

    client.force_authenticate(user=MockUser())

    response = client.get(reverse("openapi-schema"), content_type="application/vnd.oai.openapi")

    assert response.data == {
        "components": {
            "schemas": {
                "DeprecatedInput": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "name",
                        "age",
                    ],
                    "type": "object",
                },
                "DeprecatedOutput": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "email": {
                            "format": "email",
                            "type": "string",
                        },
                    },
                    "required": [
                        "email",
                        "age",
                    ],
                    "type": "object",
                },
                "DeprecatedPydanticinput": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "name",
                        "age",
                    ],
                    "type": "object",
                },
                "DeprecatedPydanticoutput": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "email": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "email",
                        "age",
                    ],
                    "type": "object",
                },
                "HeaderAndCookieInput": {
                    "properties": {
                        "Cookie-Name": {
                            "nullable": True,
                            "type": "string",
                        },
                        "Header-Name": {
                            "nullable": True,
                            "type": "string",
                        },
                        "age": {
                            "type": "integer",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "name",
                        "age",
                    ],
                    "type": "object",
                },
                "HeaderAndCookieOutput": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "cookie_name": {
                            "nullable": True,
                            "type": "string",
                        },
                        "email": {
                            "format": "email",
                            "type": "string",
                        },
                        "header_name": {
                            "nullable": True,
                            "type": "string",
                        },
                    },
                    "required": [
                        "email",
                        "age",
                    ],
                    "type": "object",
                },
                "Input": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "name": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "name",
                        "age",
                    ],
                    "type": "object",
                },
                "Output": {
                    "properties": {
                        "age": {
                            "type": "integer",
                        },
                        "email": {
                            "format": "email",
                            "type": "string",
                        },
                    },
                    "required": [
                        "email",
                        "age",
                    ],
                    "type": "object",
                },
            },
            "securitySchemes": {
                "another": {
                    "scheme": "basic",
                    "type": "http",
                },
                "my_security": {
                    "bearerFormat": "JWT",
                    "scheme": "bearer",
                    "type": "http",
                },
            },
        },
        "info": {
            "contact": {
                "email": "user@example.com",
            },
            "description": "API for all things",
            "license": {
                "name": "MIT",
            },
            "termsOfService": "example.com",
            "title": "Your Project",
            "version": "1.0.0",
        },
        "openapi": "3.0.2",
        "paths": {
            "/api/example/": {
                "post": {
                    "description": "Example Input",
                    "operationId": "createInputExample",
                    "parameters": [],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Input",
                                },
                            },
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "$ref": "#/components/schemas/Input",
                                },
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "$ref": "#/components/schemas/Input",
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Output",
                                    },
                                },
                            },
                            "description": "Example Output",
                        },
                        "401": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Unauthenticated.",
                        },
                    },
                    "security": [
                        {
                            "my_security": [],
                        },
                    ],
                    "tags": [
                        "example",
                    ],
                },
            },
            "/api/example/deprecated/": {
                "post": {
                    "deprecated": True,
                    "description": "Example Input",
                    "operationId": "createDeprecatedInputExampleDeprecated",
                    "parameters": [],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeprecatedInput",
                                },
                            },
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeprecatedInput",
                                }
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "$ref": "#/components/schemas/DeprecatedInput",
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/DeprecatedOutput",
                                    },
                                },
                            },
                            "description": "Example Output",
                        },
                        "401": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Unauthenticated.",
                        },
                    },
                    "security": [
                        {
                            "my_security": [],
                        },
                    ],
                    "tags": [
                        "example",
                    ],
                },
            },
            "/api/example/headers-and-cookies/": {
                "patch": {
                    "description": "Example Input",
                    "operationId": "partialUpdateHeaderAndCookieInputExampleHeadersAndCookies",
                    "parameters": [
                        {
                            "description": "",
                            "in": "header",
                            "name": "Header-Name",
                            "required": False,
                            "schema": {
                                "type": "string",
                            },
                        },
                        {
                            "description": "",
                            "in": "cookie",
                            "name": "Cookie-Name",
                            "required": False,
                            "schema": {
                                "type": "string",
                            },
                        },
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "age": {
                                            "type": "integer",
                                        },
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                        "age",
                                    ],
                                    "type": "object",
                                },
                            },
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "properties": {
                                        "age": {
                                            "type": "integer",
                                        },
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                        "age",
                                    ],
                                    "type": "object",
                                },
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "properties": {
                                        "age": {
                                            "type": "integer",
                                        },
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                        "age",
                                    ],
                                    "type": "object",
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/HeaderAndCookieOutput",
                                    },
                                },
                            },
                            "description": "Example " "Input",
                        },
                        "401": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Unauthenticated.",
                        },
                    },
                    "security": [
                        {
                            "my_security": [],
                        },
                    ],
                    "tags": [
                        "example",
                    ],
                },
            },
            "/api/example/private/": {
                "put": {
                    "description": "Example Input",
                    "operationId": "updateInputExamplePrivate",
                    "parameters": [],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Input",
                                },
                            },
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "$ref": "#/components/schemas/Input",
                                },
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "$ref": "#/components/schemas/Input",
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Output",
                                    },
                                },
                            },
                            "description": "Example Output",
                        },
                        "401": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Unauthenticated.",
                        },
                        "403": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Permission Denied.",
                        },
                    },
                    "security": [
                        {
                            "another": [],
                        },
                    ],
                    "tags": [
                        "example",
                    ],
                },
            },
            "/api/example/{age}/": {
                "patch": {
                    "description": "Example Input",
                    "operationId": "partialUpdateInputExampleAge",
                    "parameters": [
                        {
                            "description": "",
                            "in": "path",
                            "name": "age",
                            "required": True,
                            "schema": {
                                "type": "integer",
                            },
                        },
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                    ],
                                    "type": "object",
                                },
                            },
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                    ],
                                    "type": "object",
                                },
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                    ],
                                    "type": "object",
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Output",
                                    },
                                },
                            },
                            "description": "Example Output",
                        },
                        "401": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Unauthenticated.",
                        },
                    },
                    "security": [
                        {
                            "my_security": [],
                        },
                    ],
                    "tags": [
                        "example",
                    ],
                },
            },
            "/api/pydantic/": {
                "get": {
                    "description": "Pydantic View",
                    "operationId": "retrieveDeprecatedPydanticinputPydantic",
                    "parameters": [
                        {
                            "description": "",
                            "in": "query",
                            "name": "name",
                            "required": True,
                            "schema": {
                                "type": "string",
                            },
                        },
                        {
                            "description": "",
                            "in": "query",
                            "name": "age",
                            "required": True,
                            "schema": {
                                "type": "integer",
                            },
                        },
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "age": {
                                                "type": "integer",
                                            },
                                            "email": {
                                                "type": "string",
                                            },
                                        },
                                        "required": [
                                            "email",
                                            "age",
                                        ],
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "",
                        },
                        "401": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "detail": {
                                                "default": "error message",
                                                "type": "string",
                                            },
                                        },
                                        "type": "object",
                                    },
                                },
                            },
                            "description": "Unauthenticated.",
                        },
                    },
                    "security": [
                        {
                            "my_security": [],
                        },
                    ],
                    "tags": [
                        "pydantic",
                    ],
                },
            },
        },
        "webhooks": {
            "ExampleWebhook": {
                "POST": {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "properties": {
                                        "age": {
                                            "type": "integer",
                                        },
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "name",
                                        "age",
                                    ],
                                    "type": "object",
                                },
                            },
                        },
                        "description": "Example Input",
                    },
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "properties": {
                                        "age": {
                                            "type": "integer",
                                        },
                                        "email": {
                                            "format": "email",
                                            "type": "string",
                                        },
                                    },
                                    "required": [
                                        "email",
                                        "age",
                                    ],
                                    "type": "object",
                                },
                            },
                            "description": "Example Output",
                        },
                    },
                },
            },
        },
    }
