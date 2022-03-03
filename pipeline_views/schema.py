from django.utils.encoding import smart_str
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import BaseSerializer, Serializer
from rest_framework.utils import formatting

from .serializers import DetailSerializer, MockSerializer
from .typing import Any, Container, Dict, ExternalDocs, HTTPMethod, List, Optional, Sequence, Type, Union
from .utils import is_serializer_class


__all__ = [
    "PipelineSchemaMixin",
    "PipelineSchema",
    "convert_to_schema",
]


def convert_to_schema(schema: Union[List[Any], Dict[str, Any], Any]) -> Dict[str, Any]:
    """Recursively convert a json-like object to OpenAPI example response."""

    if isinstance(schema, list):
        return {
            "type": "array",
            "items": convert_to_schema(schema[0] if len(schema) > 0 else "???"),
        }

    if isinstance(schema, dict):
        return {
            "type": "object",
            "properties": {str(key): convert_to_schema(value) for key, value in schema.items()},
        }

    return {
        "type": "string",
        "default": str(schema),
    }


class PipelineSchemaMixin:

    responses: Dict[HTTPMethod, Dict[int, Union[str, Type[BaseSerializer]]]] = {}
    query_parameters: Dict[HTTPMethod, List[str]] = {}
    deprecated: Container[HTTPMethod] = []
    security: Dict[HTTPMethod, List[Dict[str, List[str]]]] = {}
    external_docs: Dict[HTTPMethod, ExternalDocs] = {}

    def get_operation(self, path: str, method: HTTPMethod) -> Dict[str, Any]:
        operation = super().get_operation(path, method)
        if method in self.deprecated:
            operation["deprecated"] = True

        security = self.security.get(method)
        if security is not None:
            operation["security"] = security

        external_docs = self.external_docs.get(method)
        if external_docs is not None:
            operation["externalDocs"] = external_docs

        return operation

    def get_description(self, path: str, method: HTTPMethod) -> str:  # pylint: disable=W0613
        serializer_class = self.view.get_serializer_class()
        description = serializer_class.__doc__ or (self.view.__class__.__doc__ or "")
        return self._get_description_section(self.view, method, formatting.dedent(smart_str(description)))

    def get_components(self, path: str, method: HTTPMethod) -> Dict[str, Any]:  # pylint: disable=W0613
        request_serializer_class = self.view.get_serializer_class()
        response_serializer_class = self.view.get_serializer_class(output=True)

        components = {}

        for serializer_class in (DetailSerializer, request_serializer_class, response_serializer_class):
            serializer = self.view.initialize_serializer(serializer_class=serializer_class)

            if getattr(serializer, "many", False):
                serializer = getattr(serializer, "child", serializer)

            component_name = self.get_component_name(serializer)
            content = self.map_serializer(serializer)
            components.setdefault(component_name, content)

        for method_responses in self.responses.values():
            for serializer_class in method_responses.values():
                if not is_serializer_class(serializer_class):
                    continue

                serializer = self.view.initialize_serializer(serializer_class=serializer_class)

                if getattr(serializer, "many", False):
                    serializer = getattr(serializer, "child", serializer)

                component_name = self.get_component_name(serializer)
                content = self.map_serializer(serializer)
                components.setdefault(component_name, content)

        return components

    def get_responses(self, path: str, method: HTTPMethod) -> Dict[str, Any]:  # pylint: disable=W0613
        data = {}

        responses = self.responses.get(method, {})
        if not responses and method not in self.view.pipelines:
            return data

        if ... not in set(responses.values()):
            responses.setdefault(200, ...)

        for status_code, info in responses.items():
            serializer_class = DetailSerializer

            if is_serializer_class(info):
                serializer_class = info
                info = serializer_class.__doc__ or ""

            if info is ...:
                serializer_class = self.view.get_serializer_class(output=True)
                info = serializer_class.__doc__ or ""

            serializer = self.view.initialize_serializer(serializer_class=serializer_class)

            response_schema = self._get_reference(serializer)

            data[str(status_code)] = {
                "content": {"application/json": {"schema": response_schema}},
                "description": info,
            }

        return data

    def get_filter_parameters(self, path, method):
        parameters = super().get_filter_parameters(path, method)
        if method not in ["GET", "PUT", "PATCH", "DELETE"]:
            return parameters

        serializer = self.get_request_serializer(path, method)

        if getattr(serializer, "many", False):
            serializer: Serializer = getattr(serializer, "child", serializer)

        for field_name, field in serializer.fields.items():
            if method != "GET" and field_name not in self.query_parameters.get(method, []):
                continue

            parameters += [
                {
                    "name": str(field_name),
                    "required": field.required,
                    "in": "query",
                    "description": str(field.help_text) if field.help_text is not None else "",
                    "schema": self.map_field(field),
                },
            ]

        return parameters

    def _get_reference(self, serializer: BaseSerializer) -> Dict[str, Any]:
        if isinstance(serializer, MockSerializer):
            response_schema = convert_to_schema(serializer._example)  # pylint: disable=W0212

        elif getattr(serializer, "many", False):
            response_schema = {
                "type": "array",
                "items": {
                    "$ref": f"#/components/schemas/{self.get_component_name(getattr(serializer, 'child', serializer))}"
                },
            }
            paginator = self.get_paginator()
            if paginator:  # pragma: no cover
                response_schema = paginator.get_paginated_response_schema(response_schema)
        else:
            response_schema = {
                "$ref": f"#/components/schemas/{self.get_component_name(serializer)}",
            }

        return response_schema

    def get_request_serializer(self, path: str, method: HTTPMethod) -> BaseSerializer:  # pylint: disable=W0613
        return self.view.get_serializer()

    def get_response_serializer(self, path: str, method: HTTPMethod) -> BaseSerializer:  # pylint: disable=W0613
        return self.view.get_serializer(output=True)


class PipelineSchema(PipelineSchemaMixin, AutoSchema):
    def __init__(
        self,
        responses: Optional[Dict[HTTPMethod, Dict[int, Union[str, Type[BaseSerializer]]]]] = None,
        query_parameters: Optional[Dict[HTTPMethod, List[str]]] = None,
        deprecated: Optional[Container[HTTPMethod]] = None,
        security: Optional[Dict[HTTPMethod, List[Dict[str, List[str]]]]] = None,
        external_docs: Optional[Dict[HTTPMethod, ExternalDocs]] = None,
        tags: Optional[Sequence[str]] = None,
        operation_id_base: Optional[str] = None,
        component_name: Optional[str] = None,
    ):
        self.responses = responses or {}
        self.query_parameters = query_parameters or {}
        self.deprecated = deprecated or []
        self.security = security or {}
        self.external_docs = external_docs or {}
        super().__init__(tags=tags, operation_id_base=operation_id_base, component_name=component_name)
