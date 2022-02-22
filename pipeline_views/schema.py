from typing import Dict, Type, Union

from rest_framework import serializers

from .serializers import DetailSerializer
from .typing import HTTPMethod


__all__ = [
    "add_default_response",
    "PipelineSchemaMixin",
]


def add_default_response(responses):
    if ... not in set(responses.values()):
        responses.setdefault(200, ...)


class PipelineSchemaMixin:

    responses: Dict[HTTPMethod, Dict[int, Union[str, Type[serializers.Serializer]]]] = {}

    def get_components(self, path, method):
        request_serializer = self.get_request_serializer(path, method)
        response_serializer = self.get_response_serializer(path, method)

        components = {}

        component_name = self.get_component_name(DetailSerializer())
        content = self.map_serializer(DetailSerializer())
        components.setdefault(component_name, content)

        if isinstance(request_serializer, serializers.Serializer):
            component_name = self.get_component_name(request_serializer)
            content = self.map_serializer(request_serializer)
            components.setdefault(component_name, content)

        if isinstance(response_serializer, serializers.Serializer):
            component_name = self.get_component_name(response_serializer)
            content = self.map_serializer(response_serializer)
            components.setdefault(component_name, content)

            for method_responses in self.responses.values():
                for serializer_class in method_responses.values():
                    if isinstance(serializer_class, type) and issubclass(serializer_class, serializers.Serializer):
                        serializer = self.view.initialize_serializer(serializer_class=serializer_class)
                        component_name = self.get_component_name(serializer)
                        content = self.map_serializer(serializer)
                        components.setdefault(component_name, content)

        return components

    def get_responses(self, path, method):
        data = {}

        responses = self.responses.get(method, {})
        if not responses and method not in self.view.pipelines:
            return data

        add_default_response(responses)

        for status_code, info in responses.items():
            serializer_class = DetailSerializer

            if isinstance(info, type) and issubclass(info, serializers.Serializer):
                serializer_class = info
                info = serializer_class.__doc__ or ""

            if info is ...:
                serializer = self.get_response_serializer(path, method)
                info = serializer.__doc__ or ""
            else:
                serializer = self.view.initialize_serializer(serializer_class=serializer_class)

            schema = self._get_reference(serializer)

            data[str(status_code)] = {
                "content": {"application/json": {"schema": schema}},
                "description": info,
            }

        return data

    def get_request_serializer(self, path, method):  # pylint: disable=W0613
        return self.view.get_serializer()

    def get_response_serializer(self, path, method):  # pylint: disable=W0613
        return self.view.get_serializer(output=True)
