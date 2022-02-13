from rest_framework.serializers import CharField, Serializer

from .typing import Any, Dict


__all__ = [
    "MockSerializer",
    "DetailSerializer",
]


class DetailSerializer(Serializer):  # pylint: disable=W0223
    detail = CharField()


class MockSerializer(Serializer):  # pylint: disable=W0223
    """Serializer that simply passes initial data to output."""

    def to_internal_value(self, data: Any) -> Dict[str, Any]:
        return self.initial_data  # type: ignore

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        return self.initial_data  # type: ignore
