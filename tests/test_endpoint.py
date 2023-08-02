from rest_framework.test import APIClient, APIRequestFactory

from tests.project.urls import ExampleView


def test_example_endpoint__APIRequestFactory():
    factory = APIRequestFactory()
    view = ExampleView.as_view()

    request = factory.post("/api/example/", {"name": "Matti", "age": 26}, format="json")
    response = view(request)

    assert response.data == {"email": "matti@email.com", "age": 26}


def test_example_endpoint__APIClient():
    client = APIClient()

    response = client.post("/api/example/", {"name": "Matti", "age": 26}, format="json")

    assert response.data == {"email": "matti@email.com", "age": 26}


def test_openapi_endpoint():
    client = APIClient()

    response = client.get("/openapi/")

    assert response.data == {
        "components": {
            "schemas": {
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
        },
        "info": {
            "description": "API",
            "title": "API",
            "version": "",
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
                    "tags": [
                        "example",
                    ],
                },
            },
        },
    }
