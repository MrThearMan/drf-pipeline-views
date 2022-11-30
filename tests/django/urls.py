from contextlib import suppress

from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import path
from django.views.generic import TemplateView
from pydantic import BaseModel
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.schemas import get_schema_view

from pipeline_views.schema import PipelineSchema, PipelineSchemaGenerator, deprecate
from pipeline_views.serializers import HeaderAndCookieSerializer
from pipeline_views.typing import Optional
from pipeline_views.views import BasePipelineView


with suppress(Exception):
    call_command("makemigrations")
    call_command("migrate")
    if not User.objects.filter(username="x", email="user@user.com").exists():
        User.objects.create_superuser(username="x", email="user@user.com", password="x")


class InputSerializer(serializers.Serializer):
    """Example Input"""

    name = serializers.CharField()
    age = serializers.IntegerField()


class OutputSerializer(serializers.Serializer):
    """Example Output"""

    email = serializers.EmailField()
    age = serializers.IntegerField()


class HeaderAndCookieInputSerializer(HeaderAndCookieSerializer):
    """Example Input"""

    take_from_headers = ["Header-Name"]
    take_from_cookies = ["Cookie-Name"]

    name = serializers.CharField()
    age = serializers.IntegerField()


class HeaderAndCookieOutputSerializer(serializers.Serializer):
    """Example Input"""

    email = serializers.EmailField()
    age = serializers.IntegerField()
    header_name = serializers.CharField(allow_null=True, required=False, allow_blank=True)
    cookie_name = serializers.CharField(allow_null=True, required=False, allow_blank=True)


class PydanticInput(BaseModel):
    name: str
    age: int


class PydanticOutput(BaseModel):
    email: str
    age: int


def example_method(name: str, age: int):
    return {"email": f"{name.lower()}@email.com", "age": age}


def example_header_and_cookie_method(name: str, age: int, header_name: Optional[str], cookie_name: Optional[str]):
    return {"email": f"{name.lower()}@email.com", "age": age, "header_name": header_name, "cookie_name": cookie_name}


class ExampleView(BasePipelineView):
    """Example View"""

    pipelines = {
        "POST": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }


class ExampleWebhook(BasePipelineView):
    """Example Webhook"""

    pipelines = {
        "POST": [
            InputSerializer,
            OutputSerializer,
        ],
    }


class ExamplePathView(BasePipelineView):
    """Example Path View"""

    pipelines = {
        "PATCH": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }

    schema = PipelineSchema(
        public={
            "PATCH": True,
        },
    )


class ExampleHeaderAndCookieView(BasePipelineView):
    """Example Header View"""

    pipelines = {
        "PATCH": [
            HeaderAndCookieInputSerializer,
            example_header_and_cookie_method,
            HeaderAndCookieOutputSerializer,
        ],
    }

    schema = PipelineSchema(
        public={
            "PATCH": True,
        },
    )


class ExamplePrivateView(BasePipelineView):
    """Example View"""

    permission_classes = [IsAuthenticated]

    pipelines = {
        "PUT": [
            InputSerializer,
            example_method,
            OutputSerializer,
        ],
    }

    schema = PipelineSchema(
        public={
            "PUT": False,
        },
    )


@deprecate(methods=["PATCH"])
class PydanticView(BasePipelineView):
    """Pydantic View"""

    pipelines = {
        "GET": [
            PydanticInput,
            example_method,
            PydanticOutput,
        ],
    }


urlpatterns = [
    path("api/example/", ExampleView.as_view(), name="test_view"),
    path("api/example/deprecated", deprecate(ExampleView).as_view(), name="test_view_deprecated"),
    path("api/example/<int:age>", ExamplePathView.as_view(), name="test_path_view"),
    path("api/example/headers-and-cookies", ExampleHeaderAndCookieView.as_view(), name="test_header_and_cookie_view"),
    path("api/example/private", ExamplePrivateView.as_view(), name="test_private_view"),
    path("api/pydantic", PydanticView.as_view(), name="test_pydantic_view"),
    path(
        "openapi/",
        get_schema_view(
            title="Your Project",
            description="API for all things",
            version="1.0.0",
            url="api",
            generator_class=PipelineSchemaGenerator.configure(
                webhooks={
                    "ExampleWebhook": {
                        "method": "POST",
                        "request_data": InputSerializer,
                        "responses": {
                            200: OutputSerializer,
                        },
                    },
                },
                contact={"email": "user@example.com"},
                license={"name": "MIT"},
                terms_of_service="example.com",
                security_schemes={
                    "my_security": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    },
                    "another": {
                        "type": "http",
                        "scheme": "basic",
                    },
                },
                security_rules={
                    AllowAny: {
                        "my_security": [],
                    },
                    (IsAuthenticated,): {
                        "another": [],
                    },
                },
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
