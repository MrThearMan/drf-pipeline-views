from django.urls import path
from django.views.generic import TemplateView
from rest_framework import serializers
from rest_framework.schemas import get_schema_view

from pipeline_views.schema import VersionSchemaGenerator
from pipeline_views.views import BasePipelineView


class InputSerializer(serializers.Serializer):
    """Example Input"""

    name = serializers.CharField()
    age = serializers.IntegerField()


class OutputSerializer(serializers.Serializer):
    """Example Output"""

    email = serializers.EmailField()
    age = serializers.IntegerField()


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


class ExamplePathView(BasePipelineView):
    """Example View"""

    pipelines = {
        "PATCH": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }


urlpatterns = [
    path("api/example/", ExampleView.as_view(), name="test_view"),
    path("api/example/<int:age>", ExamplePathView.as_view(), name="test_path_view"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
            url="api",
            generator_class=VersionSchemaGenerator.with_info(
                contact={"email": "user@example.com"},
                license={"name": "MIT"},
                terms_of_service="example.com",
            ),
        ),
        name="openapi-schema",
    ),
    path(
        "swagger-ui/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
]
