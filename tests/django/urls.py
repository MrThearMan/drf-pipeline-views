try:
    from django.urls import re_path
except ImportError:
    from django.conf.urls import url as re_path

from rest_framework import serializers

from pipeline_views.mixins import PostMixin
from pipeline_views.views import BaseAPIView


class InputSerializer(serializers.Serializer):
    name = serializers.CharField()
    age = serializers.IntegerField()


class OutputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    id = serializers.UUIDField()


def test_method(name: str, age: int):
    return {"email": f"{name.lower()}@email.com", "age": age}


class ExampleView(PostMixin, BaseAPIView):

    pipelines = {
        "POST": (test_method,),
    }


urlpatterns = [
    re_path(r"^$", ExampleView.as_view(), name="test_view"),
]
