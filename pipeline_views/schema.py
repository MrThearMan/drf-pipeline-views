import uritemplate  # pylint: disable=E0401
from django.utils.encoding import smart_str
from rest_framework.fields import Field
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
    prefix: str = ""

    def get_operation(self, path: str, method: HTTPMethod) -> Dict[str, Any]:
        operation = {}

        operation["operationId"] = self.get_operation_id(path, method)
        operation["description"] = self.get_description(path, method)

        parameters: Dict[str, Dict[str, Any]] = self.get_path_parameters(path, method)
        for name, params in self.get_filter_parameters(path, method).items():
            parameters.setdefault(name, params)

        operation["parameters"] = list(parameters.values())

        request_body = self.get_request_body(path, method)
        if request_body:
            operation["requestBody"] = request_body

        operation["responses"] = self.get_responses(path, method)
        operation["tags"] = self.get_tags(path, method)

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

    def get_request_body(self, path: str, method: HTTPMethod) -> Dict[str, Any]:
        if method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return {}

        serializer = self.get_request_serializer(path, method)

        query_params = self.query_parameters.get(method, {})
        path_params = uritemplate.variables(path)
        params = list(query_params) + list(path_params)

        if params:
            new_serializer_class = type(
                serializer.__class__.__name__,
                (MockSerializer,),
                {key: value for key, value in serializer.fields.items() if key not in params},
            )
            new_serializer_class.__doc__ = serializer.__class__.__doc__
            serializer = new_serializer_class()

        item_schema = self._get_reference(serializer)

        return {"content": {"application/json": {"schema": item_schema}}}

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

                if getattr(serializer_class, "many", False):
                    data.setdefault(
                        "204",
                        {
                            "content": {"application/json": {"type": "string", "default": ""}},
                            "description": "No Results",
                        },
                    )

                info = serializer_class.__doc__ or ""

            serializer = self.view.initialize_serializer(serializer_class=serializer_class)

            response_schema = self._get_reference(serializer)

            data[str(status_code)] = {
                "content": {"application/json": {"schema": response_schema}},
                "description": info,
            }

        return data

    def get_tags(self, path: str, method: HTTPMethod) -> List[str]:  # pylint: disable=W0613
        if self._tags:
            return self._tags

        if path.startswith("/"):
            path = path[1:]

        if path.startswith(self.prefix):
            path = path[len(self.prefix) :]

        return [path.split("/")[0].replace("_", "-")]

    def get_path_parameters(self, path: str, method: HTTPMethod) -> Dict[str, Dict[str, Any]]:
        parameters: Dict[str, Dict[str, Any]] = {}

        serializer = self.get_request_serializer(path, method)
        if getattr(serializer, "many", False):
            serializer: Serializer = getattr(serializer, "child", serializer)

        for variable in uritemplate.variables(path):
            description = ""
            schema = {"type": "string"}

            field: Optional[Field] = serializer.fields.get(variable)
            if field is not None:
                description = str(field.help_text) if field.help_text is not None else ""
                schema = self.map_field(field)

            parameters[variable] = {
                "name": variable,
                "in": "path",
                "required": True,
                "description": description,
                "schema": schema,
            }

        return parameters

    def get_filter_parameters(self, path: str, method: HTTPMethod) -> Dict[str, Dict[str, Any]]:
        parameters: Dict[str, Dict[str, Any]] = {}
        if method not in {"GET", "PUT", "PATCH", "DELETE"}:
            return parameters

        serializer = self.get_request_serializer(path, method)
        if getattr(serializer, "many", False):
            serializer: Serializer = getattr(serializer, "child", serializer)

        for field_name, field in serializer.fields.items():
            if method != "GET" and field_name not in self.query_parameters.get(method, []):
                continue

            parameters[str(field_name)] = {
                "name": str(field_name),
                "required": field.required,
                "in": "query",
                "description": str(field.help_text) if field.help_text is not None else "",
                "schema": self.map_field(field),
            }

        return parameters

    def _get_reference(self, serializer: BaseSerializer) -> Dict[str, Any]:
        if isinstance(serializer, MockSerializer):
            if serializer.fields:
                response_schema = self.map_serializer(serializer)
            else:
                response_schema = convert_to_schema(serializer._example)  # pylint: disable=W0212

        elif getattr(serializer, "many", False):
            response_schema = {
                "type": "array",
                "items": {
                    "$ref": f"#/components/schemas/{self.get_component_name(getattr(serializer, 'child', serializer))}"
                },
            }
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
        prefix: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        operation_id_base: Optional[str] = None,
        component_name: Optional[str] = None,
    ):
        self.responses = responses or self.responses
        self.query_parameters = query_parameters or self.query_parameters
        self.deprecated = deprecated or self.deprecated
        self.security = security or self.security
        self.external_docs = external_docs or self.external_docs
        self.prefix = prefix or self.prefix
        super().__init__(tags=tags, operation_id_base=operation_id_base, component_name=component_name)
