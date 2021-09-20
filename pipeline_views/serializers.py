from rest_framework.serializers import Serializer

from .typing import Any, Dict


__all__ = [
    "MockSerializer",
]


class MockSerializer(Serializer):
    """Serializer that simply passes initial data to output."""

    def to_internal_value(self, data: Any) -> Dict[str, Any]:
        return self.initial_data

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        return self.initial_data

    def create(self, validated_data: Any) -> Any:
        """Creted to satisty linters."""

    def update(self, instance: Any, validated_data: Any) -> Any:
        """Creted to satisty linters."""
