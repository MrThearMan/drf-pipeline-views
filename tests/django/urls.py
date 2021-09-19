from uuid import uuid4

from django.contrib import admin
from django.urls import path
from rest_framework import serializers

from pipeline_views.mixins import DeleteMixin, GetMixin, PostMixin, PutMixin
from pipeline_views.serializers import MockSerializer
from pipeline_views.views import BaseAPIView


class InputSerializer(serializers.Serializer):
    name = serializers.CharField()
    age = serializers.IntegerField()


class OutputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    id = serializers.UUIDField()


def test_method(name: str, age: int):
    return {"email": f"Me@email.com", "id": str(uuid4())}


class TestView(PostMixin, BaseAPIView):

    pipelines = {
        "POST": (test_method,),
    }


urlpatterns = [
    path("", TestView.as_view(), name="test_view"),
    path("admin/", admin.site.urls),
]
