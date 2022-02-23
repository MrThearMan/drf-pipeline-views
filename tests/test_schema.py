from rest_framework.fields import CharField
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import Serializer

from pipeline_views.schema import PipelineSchemaMixin, add_default_response
from tests.django.urls import ExampleView


def test_add_default_response():
    responses = {}
    add_default_response(responses)
    assert responses == {200: ...}


def test_add_default_response__ellipeses_exists():
    responses = {204: ...}
    add_default_response(responses)
    assert responses == {204: ...}


def test_add_default_response__status_code_exists():
    responses = {200: "foo"}
    add_default_response(responses)
    assert responses == {200: "foo"}


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

    class CustomSchema(PipelineSchemaMixin, AutoSchema):
        responses = {
            "POST": {
                200: ...,
                400: "Unavailable",
                404: CustomSerializer,
            },
        }

    class CustomView(ExampleView):
        """Custom View"""

        schema = CustomSchema()

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


def test_pipeline_schema__example__get_responses(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomSchema(PipelineSchemaMixin, AutoSchema):
        responses = {
            "POST": {
                200: ...,
                400: "Unavailable",
                404: CustomSerializer,
            },
        }

    class CustomView(ExampleView):
        """Custom View"""

        schema = CustomSchema()

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
    class CustomSchema(PipelineSchemaMixin, AutoSchema):
        pass

    class CustomView(ExampleView):
        """Custom View"""

        schema = CustomSchema()

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
    class CustomSchema(PipelineSchemaMixin, AutoSchema):
        pass

    class CustomView(ExampleView):
        """Custom View"""

        schema = CustomSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    components = view.schema.get_responses("", "GET")
    assert components == {}


def test_pipeline_schema__example__get_operation(drf_request):
    class CustomSerializer(Serializer):
        """This is the description"""

        data = CharField()

    class CustomSchema(PipelineSchemaMixin, AutoSchema):
        responses = {
            "POST": {
                200: ...,
                400: "Unavailable",
                404: CustomSerializer,
            },
        }
        deprecated = {"POST": True}
        security = {"POST": [{"foo": ["bar"]}]}
        external_docs = {"POST": {"description": "foo", "url": "bar"}}

    class CustomView(ExampleView):
        """Custom View"""

        schema = CustomSchema()

    view = CustomView()
    view.request = drf_request
    view.request.method = "POST"
    view.format_kwarg = None
    responses = view.schema.get_operation("", "POST")
    assert responses == {
        "deprecated": True,
        "externalDocs": {
            "description": "foo",
            "url": "bar",
        },
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
        "summary": "Example Input",
        "tags": [""],
    }
