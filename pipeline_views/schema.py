from django.utils.encoding import smart_str
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import BaseSerializer
from rest_framework.utils import formatting

from .serializers import DetailSerializer
from .typing import Any, Dict, ExternalDocs, HTTPMethod, List, Type, Union
from .utils import is_serializer_class


__all__ = [
    "add_default_response",
    "PipelineSchemaMixin",
    "PipelineSchema",
]


def add_default_response(responses):
    if ... not in set(responses.values()):
        responses.setdefault(200, ...)


class PipelineSchemaMixin(AutoSchema):

    responses: Dict[HTTPMethod, Dict[int, Union[str, Type[BaseSerializer]]]] = {}
    deprecated: Dict[HTTPMethod, bool] = {}
    security: Dict[HTTPMethod, List[Dict[str, List[str]]]] = {}
    external_docs: Dict[HTTPMethod, ExternalDocs] = {}

    def get_operation(self, path: str, method: HTTPMethod) -> Dict[str, Any]:
        operation = super().get_operation(path, method)
        if self.deprecated.get(method):
            operation["deprecated"] = True

        security = self.security.get(method)
        if security is not None:
            operation["security"] = security

        external_docs = self.external_docs.get(method)
        if external_docs is not None:
            operation["externalDocs"] = external_docs

        operation["summary"] = operation.pop("description", "")
        return operation

    def get_description(self, path: str, method: HTTPMethod) -> str:
        serializer = self.get_request_serializer(path, method)
        description = serializer.__class__.__doc__ or (self.view.__class__.__doc__ or "")
        return self._get_description_section(self.view, method, formatting.dedent(smart_str(description)))

    def get_components(self, path: str, method: HTTPMethod) -> Dict[str, Any]:
        request_serializer = self.get_request_serializer(path, method)
        response_serializer = self.get_response_serializer(path, method)

        components = {}

        for serializer in (DetailSerializer(), request_serializer, response_serializer):
            component_name = self.get_component_name(serializer)
            content = self.map_serializer(serializer)
            components.setdefault(component_name, content)

        for method_responses in self.responses.values():
            for serializer_class in method_responses.values():
                if is_serializer_class(serializer_class):
                    serializer = self.view.initialize_serializer(serializer_class=serializer_class)
                    component_name = self.get_component_name(serializer)
                    content = self.map_serializer(serializer)
                    components.setdefault(component_name, content)

        return components

    def get_responses(self, path: str, method: HTTPMethod) -> Dict[str, Any]:
        data = {}

        responses = self.responses.get(method, {})
        if not responses and method not in self.view.pipelines:
            return data

        add_default_response(responses)

        for status_code, info in responses.items():
            serializer_class = DetailSerializer

            if is_serializer_class(info):
                serializer_class = info
                info = serializer_class.__doc__ or ""

            if info is ...:
                serializer = self.get_response_serializer(path, method)
                info = serializer.__class__.__doc__ or ""
            else:
                serializer = self.view.initialize_serializer(serializer_class=serializer_class)

            schema = self._get_reference(serializer)

            data[str(status_code)] = {
                "content": {"application/json": {"schema": schema}},
                "description": info,
            }

        return data

    def get_request_serializer(self, path: str, method: HTTPMethod) -> BaseSerializer:  # pylint: disable=W0613
        return self.view.get_serializer()

    def get_response_serializer(self, path: str, method: HTTPMethod) -> BaseSerializer:  # pylint: disable=W0613
        return self.view.get_serializer(output=True)


class PipelineSchema(PipelineSchemaMixin, AutoSchema):
    pass
