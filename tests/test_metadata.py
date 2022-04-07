from rest_framework import serializers

from pipeline_views import BasePipelineView


def test_metadata_class(drf_request):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField(help_text="Help")
        age = serializers.IntegerField()

    class OutputSerializer(serializers.Serializer):
        email = serializers.EmailField(help_text="Text")
        age = serializers.IntegerField()

    class TestView(BasePipelineView):
        """This is the description"""

        pipelines = {
            "GET": [
                InputSerializer,
                OutputSerializer,
            ]
        }

    drf_request.method = "GET"

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "GET"

    result = view.options(drf_request)

    assert result.data == {
        "name": "Test",
        "description": "This is the description",
        "renders": [
            "application/json",
            "text/html",
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ],
        "actions": {
            "GET": {
                "input": {
                    "name": {
                        "type": "string",
                        "required": True,
                        "help_text": "Help",
                    },
                    "age": {
                        "type": "integer",
                        "required": True,
                    },
                },
                "output": {
                    "email": {
                        "type": "email",
                        "required": True,
                        "help_text": "Text",
                    },
                    "age": {
                        "type": "integer",
                        "required": True,
                    },
                },
            }
        },
    }


def test_metadata_class__output_list(drf_request):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField()

    class OutputSerializer(serializers.Serializer):
        many = True

        email = serializers.EmailField()
        age = serializers.IntegerField()

    class TestView(BasePipelineView):
        """This is the description"""

        pipelines = {
            "GET": [
                InputSerializer,
                OutputSerializer,
            ]
        }

    drf_request.method = "GET"

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "GET"

    result = view.options(drf_request)

    assert result.data == {
        "name": "Test",
        "description": "This is the description",
        "renders": [
            "application/json",
            "text/html",
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ],
        "actions": {
            "GET": {
                "input": {
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "age": {
                        "type": "integer",
                        "required": True,
                    },
                },
                "output": [
                    {
                        "email": {
                            "type": "email",
                            "required": True,
                        },
                        "age": {
                            "type": "integer",
                            "required": True,
                        },
                    }
                ],
            }
        },
    }


def test_metadata_class__child_fields(drf_request):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField()

    class OutputSerializer(serializers.Serializer):
        emails = serializers.ListField(child=serializers.EmailField())
        ages = serializers.DictField(child=serializers.IntegerField())

    class TestView(BasePipelineView):
        """This is the description"""

        pipelines = {
            "GET": [
                InputSerializer,
                OutputSerializer,
            ]
        }

    drf_request.method = "GET"

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "GET"

    result = view.options(drf_request)

    assert result.data == {
        "name": "Test",
        "description": "This is the description",
        "renders": [
            "application/json",
            "text/html",
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ],
        "actions": {
            "GET": {
                "input": {
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "age": {
                        "type": "integer",
                        "required": True,
                    },
                },
                "output": {
                    "emails": [
                        {
                            "type": "email",
                            "required": True,
                        }
                    ],
                    "ages": {
                        "<key>": {
                            "type": "integer",
                            "required": True,
                        }
                    },
                },
            }
        },
    }


def test_metadata_class__serializer_field(drf_request):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField()

    class DataSerializer(serializers.Serializer):
        email = serializers.EmailField()
        age = serializers.IntegerField()

    class OutputSerializer(serializers.Serializer):
        data = DataSerializer()

    class TestView(BasePipelineView):
        """This is the description"""

        pipelines = {
            "GET": [
                InputSerializer,
                OutputSerializer,
            ]
        }

    drf_request.method = "GET"

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "GET"

    result = view.options(drf_request)

    assert result.data == {
        "name": "Test",
        "description": "This is the description",
        "renders": [
            "application/json",
            "text/html",
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ],
        "actions": {
            "GET": {
                "input": {
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "age": {
                        "type": "integer",
                        "required": True,
                    },
                },
                "output": {
                    "data": {
                        "email": {
                            "type": "email",
                            "required": True,
                        },
                        "age": {
                            "type": "integer",
                            "required": True,
                        },
                    }
                },
            }
        },
    }


def test_metadata_class_choise_field(drf_request):
    class InputSerializer(serializers.Serializer):
        name = serializers.CharField()
        age = serializers.IntegerField()

    class OutputSerializer(serializers.Serializer):
        items = serializers.ChoiceField(choices=["foo", "bar"])

    class TestView(BasePipelineView):
        """This is the description"""

        pipelines = {
            "GET": [
                InputSerializer,
                OutputSerializer,
            ]
        }

    drf_request.method = "GET"

    view = TestView()
    view.request = drf_request
    view.format_kwarg = None
    view.request.method = "GET"

    result = view.options(drf_request)

    assert result.data == {
        "name": "Test",
        "description": "This is the description",
        "renders": [
            "application/json",
            "text/html",
        ],
        "parses": [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ],
        "actions": {
            "GET": {
                "input": {
                    "name": {
                        "type": "string",
                        "required": True,
                    },
                    "age": {
                        "type": "integer",
                        "required": True,
                    },
                },
                "output": {
                    "items": {
                        "type": "choice",
                        "required": True,
                        "choices": ["foo", "bar"],
                    },
                },
            }
        },
    }
