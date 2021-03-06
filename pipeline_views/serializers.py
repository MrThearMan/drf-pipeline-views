from rest_framework.serializers import Serializer

from .typing import Any, Dict, List, Type, Union


__all__ = [
    "EmptySerializer",
    "MockSerializer",
]


class EmptySerializer(Serializer):  # pylint: disable=W0223
    # Used for schema 204 responses
    pass


class MockSerializer(Serializer):  # pylint: disable=W0223
    # Serializer that simply passes initial data to output.

    _example: Union[List[Any], Dict[str, Any], Any] = {}

    @classmethod
    def with_example(cls, description: str, response: Union[List[Any], Dict[str, Any], Any]) -> Type["MockSerializer"]:
        """Sets OpenAPI example response."""
        new_cls = type(MockSerializer.__name__, (cls,), {"_example": response})  # type: ignore
        new_cls.__doc__ = description
        return new_cls  # type: ignore

    def to_internal_value(self, data: Any) -> Dict[str, Any]:
        return self.initial_data  # type: ignore

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        return self.initial_data  # type: ignore
