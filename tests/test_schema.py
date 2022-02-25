from rest_framework.fields import CharField, IntegerField
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import Serializer

from pipeline_views import MockSerializer
from pipeline_views.schema import PipelineSchema
from tests.django.urls import ExampleView, InputSerializer, OutputSerializer


def test_pipeline_schema__get_components(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    components = view.schema.get_components("", "")
    assert components == {
        "Detail": {
            "properties": {
                "detail": {
                    "type": "string",
                },
            },
            "required": ["detail"],
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


def test_pipeline_schema__get_responses(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("", "POST")
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
        }
    }


def test_pipeline_schema__example__get_components(drf_request):
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
    components = view.schema.get_components("", "POST")
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
        "Detail": {
            "properties": {
                "detail": {
                    "type": "string",
                },
            },
            "required": ["detail"],
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


def test_pipeline_schema__example__get_components__list(drf_request):
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
    components = view.schema.get_components("", "POST")
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
        "Detail": {
            "properties": {
                "detail": {
                    "type": "string",
                },
            },
            "required": ["detail"],
            "type": "object",
        },
        "Example": {
            "properties": {
                "data": {
                    "type": "integer",
                },
            },
            "required": ["data"],
            "type": "object",
        },
    }


def test_pipeline_schema__example__get_responses(drf_request):
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
    responses = view.schema.get_responses("", "POST")
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
                        "$ref": "#/components/schemas/Detail",
                    },
                },
            },
            "description": "Unavailable",
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


def test_pipeline_schema__example__get_responses__none(drf_request):
    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("", "POST")
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
    }


def test_pipeline_schema__example__get_responses__wrong_method(drf_request):
    class CustomView(ExampleView):
        """Custom View"""

        schema = PipelineSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_responses("", "GET")
    assert responses == {}


def test_pipeline_schema__example__get_responses__list(drf_request):
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
    responses = view.schema.get_responses("", "POST")
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
                        "$ref": "#/components/schemas/Detail",
                    },
                },
            },
            "description": "Unavailable",
        },
        "404": {
            "content": {
                "application/json": {
                    "schema": {
                        "items": {
                            "$ref": "#/components/schemas/Custom",
                        },
                        "type": "array",
                    },
                }
            },
            "description": "This is the description",
        },
    }


def test_pipeline_schema__example__get_responses__mock_serializer(drf_request):
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
    responses = view.schema.get_responses("", "POST")
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
                            }
                        },
                        "type": "object",
                    }
                }
            },
            "description": "This is the response",
        },
        "400": {
            "content": {
                "application/json": {
                    "schema": {
                        "$ref": "#/components/schemas/Detail",
                    },
                },
            },
            "description": "Unavailable",
        },
        "404": {
            "content": {
                "application/json": {
                    "schema": {
                        "items": {
                            "$ref": "#/components/schemas/Custom",
                        },
                        "type": "array",
                    },
                }
            },
            "description": "This is the description",
        },
    }


def test_pipeline_schema__example__get_operation(drf_request):
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
            },
            deprecated=["POST"],
            security={
                "POST": [{"foo": ["bar"]}],
            },
            external_docs={
                "POST": {"description": "foo", "url": "bar"},
            },
        )

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    operation = view.schema.get_operation("", "POST")
    assert operation == {
        "deprecated": True,
        "description": "Example Input",
        "externalDocs": {"description": "foo", "url": "bar"},
        "operationId": "createInput",
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
            }
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
            "400": {
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/Detail",
                        },
                    },
                },
                "description": "Unavailable",
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
    }


def test_pipeline_schema__example__get_request_serializer(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    serializer = view.schema.get_request_serializer("", "POST")
    assert serializer.__class__ == InputSerializer


def test_pipeline_schema__example__get_response_serializer(drf_request):
    view = ExampleView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    serializer = view.schema.get_response_serializer("", "POST")
    assert serializer.__class__ == OutputSerializer
