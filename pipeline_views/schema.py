import uritemplate  # pylint: disable=E0401
from django.utils.encoding import smart_str
from rest_framework.fields import Field
from rest_framework.request import Request
from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator
from rest_framework.serializers import BaseSerializer, Serializer
from rest_framework.utils import formatting

from .serializers import EmptySerializer, MockSerializer
from .typing import (
    Any,
    APIContact,
    APIInfo,
    APILicense,
    APISchema,
    Container,
    Dict,
    ExternalDocs,
    HTTPMethod,
    List,
    Optional,
    Sequence,
    SerializerType,
    Type,
    Union,
)
from .utils import is_serializer_class


__all__ = [
    "PipelineSchemaMixin",
    "PipelineSchema",
    "VersionEndpointEnumerator",
    "VersionSchemaGeneratorMixin",
    "VersionSchemaGenerator",
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

        for serializer_class in (request_serializer_class, response_serializer_class):
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

        request_media_types = self.map_parsers(path, method)
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

        return {"content": {content_type: item_schema for content_type in request_media_types}}

    def get_responses(self, path: str, method: HTTPMethod) -> Dict[str, Any]:  # pylint: disable=W0613
        data = {}
        response_media_types = self.map_renderers(path, method)

        responses = self.responses.get(method, {})
        if not responses and method not in self.view.pipelines:
            return data

        if ... not in set(responses.values()):
            responses.setdefault(200, ...)

        for status_code, info in responses.items():
            serializer_class: Optional[SerializerType] = None

            if info is ...:
                serializer_class = self.view.get_serializer_class(output=True)
                info = serializer_class.__doc__ or ""

                if getattr(serializer_class, "many", False):
                    data.setdefault("204", self._get_no_result_schema())

            elif is_serializer_class(info):
                serializer_class = info
                info = serializer_class.__doc__ or ""

            if serializer_class is not None:
                serializer = self.view.initialize_serializer(serializer_class=serializer_class)

                if isinstance(serializer, EmptySerializer):
                    status_code = 204

                response_schema = self._get_reference(serializer)
            else:
                response_schema = {"schema": self._get_error_message_schema()}

            data[str(status_code)] = {
                "content": {content_type: response_schema for content_type in response_media_types},
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
                response_schema = {"schema": self.map_serializer(serializer)}
            else:
                response_schema = {"schema": convert_to_schema(serializer._example)}  # pylint: disable=W0212

        elif isinstance(serializer, EmptySerializer):
            response_schema = self._get_no_result_schema()

        elif getattr(serializer, "many", False):
            response_schema = {
                "schema": {
                    "type": "array",
                    "items": {
                        "$ref": (
                            f"#/components/schemas/"
                            f"{self.get_component_name(getattr(serializer, 'child', serializer))}"
                        )
                    },
                },
            }
        else:
            response_schema = {
                "schema": {
                    "$ref": f"#/components/schemas/{self.get_component_name(serializer)}",
                },
            }

        return response_schema

    @staticmethod
    def _get_no_result_schema(description: str = "No Results") -> Dict[str, Any]:
        return {
            "content": {"application/json": {"type": "string", "default": ""}},
            "description": description,
        }

    @staticmethod
    def _get_error_message_schema(error_message: str = "Error message") -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"detail": {"type": "string", "default": error_message}},
        }

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


class VersionEndpointEnumerator(EndpointEnumerator):

    url: str = ""

    def get_path_from_regex(self, path_regex: str) -> str:
        reg = super().get_path_from_regex(path_regex)
        url = self.url

        if reg.startswith("/"):
            reg = reg[1:]
        if url.startswith("/"):
            url = url[1:]

        if reg[: len(url)] == url:
            return reg[len(url) :]

        return reg


class VersionSchemaGeneratorMixin(SchemaGenerator):

    contact: APIContact = {}
    license: APILicense = {}
    terms_of_service: str = ""

    endpoint_inspector_cls = VersionEndpointEnumerator

    @classmethod
    def with_info(
        cls,
        contact: Optional[APIContact] = None,
        license: Optional[APILicense] = None,  # pylint: disable=redefined-builtin
        terms_of_service: Optional[str] = None,
    ) -> Type[SchemaGenerator]:
        return type(  # type: ignore
            cls.__name__,
            (cls,),
            {
                "contact": contact or cls.contact,
                "license": license or cls.license,
                "terms_of_service": terms_of_service or cls.terms_of_service,
            },
        )

    def get_info(self) -> APIInfo:
        info: APIInfo = super().get_info()  # type: ignore
        if self.contact:
            info["contact"] = self.contact
        if self.license:
            info["license"] = self.license
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service
        return info

    def get_schema(self, request: Optional[Request] = None, public: bool = False) -> APISchema:
        schema: APISchema = super().get_schema(request, public)  # type: ignore

        sorted_paths = {}
        for path, operations in schema["paths"].items():
            tag = list(operations.values())[0]["tags"][0]
            sorted_paths.setdefault(tag, {})
            sorted_paths[tag][path] = operations

        schema["paths"] = {
            path: operations
            for endpoints in dict(sorted(sorted_paths.items())).values()
            for path, operations in dict(sorted(endpoints.items())).items()
        }

        return schema


class VersionSchemaGenerator(VersionSchemaGeneratorMixin, SchemaGenerator):
    def __init__(
        self,
        title: Optional[str] = None,
        url: Optional[str] = None,
        description: Optional[str] = None,
        patterns: Optional[List[str]] = None,
        urlconf: Optional[str] = None,
        version: Optional[str] = None,
        contact: Optional[APIContact] = None,
        license: Optional[APILicense] = None,  # pylint: disable=redefined-builtin
        terms_of_service: Optional[str] = None,
    ):
        """Create a versioned schema.

        :param title: The name of the API (required).
        :param url: The root URL of the API schema. This option is not required unless
                    the schema is included under path prefix.
        :param description: Longer descriptive text.
        :param patterns: A list of URLs to inspect when generating the schema.
                         Defaults to the project's URL conf.
        :param urlconf: A URL conf module name to use when generating the schema.
                        Defaults to settings.ROOT_URLCONF.
        :param version: The version of the API. Defaults to 0.1.0.
        :param contact: API developer contact information.
        :param license: API license information.
        :param terms_of_service: API terms of service link.
        """

        if url and not url.startswith("/"):
            url = "/" + url

        super().__init__(
            title=title,
            url=url,
            description=description,
            patterns=patterns,
            urlconf=urlconf,
            version=version,
        )

        self.endpoint_inspector_cls.url = self.url or ""
        self.contact = contact or self.contact
        self.license = license or self.license
        self.terms_of_service = terms_of_service or self.terms_of_service
