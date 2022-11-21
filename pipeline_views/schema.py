# pylint: disable=too-many-lines
from __future__ import annotations

import copy
import re
import warnings
from decimal import Decimal
from functools import partial
from urllib.parse import urljoin

from django.core import validators
from django.utils.encoding import smart_str
from rest_framework import serializers
from rest_framework.fields import _UnvalidatedField, empty
from rest_framework.permissions import AllowAny
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.request import Request
from rest_framework.schemas.generators import BaseSchemaGenerator, EndpointEnumerator
from rest_framework.schemas.inspectors import ViewInspector
from rest_framework.settings import api_settings
from rest_framework.utils import formatting

from .inference import serializer_from_callable, snake_case_to_camel_case
from .serializers import EmptySerializer, HeaderAndCookieSerializer, MockSerializer
from .typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    HTTPMethod,
    List,
    Literal,
    Optional,
    PathAndMethod,
    SchemaCallbackData,
    SchemaWebhook,
    SecurityRules,
    SerializerType,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from .typing.openapi import (
    APIContact,
    APIExternalDocumentation,
    APIInfo,
    APILicense,
    APILinks,
    APIOperation,
    APIParameter,
    APIPathItem,
    APIRequestBody,
    APIResponses,
    APISchema,
    APISecurityScheme,
    APIType,
    OpenAPI,
)
from .utils import get_path_parameters, is_serializer_class


if TYPE_CHECKING:
    from .views import BasePipelineView

    T = TypeVar("T", bound=Type[BasePipelineView])


__all__ = [
    "convert_to_schema",
    "deprecate",
    "PipelineSchema",
    "PipelineSchemaGenerator",
]


SerializerOrSerializerType = Union[serializers.Serializer, Type[serializers.Serializer]]
serializer_pattern = re.compile("serializer", re.IGNORECASE)


def deprecate(__view: Optional[T] = None, *, methods: Optional[List[HTTPMethod]] = None) -> T:
    """Deprecate a view in the OpenAPI schema while retaining the original.

    :param methods: HTTP methods to deprecate. Deprecate all if not given.
    """

    def view(_view: T, _methods: Optional[List[HTTPMethod]] = None):
        # Mock the "get_serializer_class" method to change the calculated "operation_id"
        def new_get_serializer_class(old_method):
            def inner(self, output: bool = False):
                serializer = old_method.__get__(self, new_view)(output)  # pylint: disable=unnecessary-dunder-call
                new_serializer = type(f"Deprecated{serializer.__name__}", (serializer,), {})
                new_serializer.__doc__ = serializer.__doc__ or ""
                return new_serializer

            return inner

        new_view: T = type(f"Deprecated{_view.__name__}", (_view,), {})  # type: ignore
        new_view.__doc__ = _view.__doc__ or ""
        new_view.get_serializer_class = new_get_serializer_class(new_view.get_serializer_class)

        if _methods is None:
            _methods = list(new_view.pipelines)

        new_view.schema = copy.deepcopy(new_view.schema)
        new_view.schema.deprecated = _methods
        return new_view

    if callable(__view):
        return view(__view, methods)  # type: ignore

    return partial(view, _methods=methods)  # type: ignore


def convert_to_schema(schema: Union[List[Any], Dict[str, Any], Any]) -> APISchema:
    """Recursively convert a json-like object to OpenAPI example response."""
    if isinstance(schema, list):
        return APISchema(
            type="array",
            items=convert_to_schema(schema[0] if len(schema) > 0 else "???"),
        )

    if isinstance(schema, dict):
        return APISchema(
            type="object",
            properties={str(key): convert_to_schema(value) for key, value in schema.items()},
        )

    return APISchema(
        type="string",
        default=str(schema),
    )


def map_field(field: serializers.Field) -> APISchema:  # pragma: no cover pylint: disable=R0911,R0912,R0915
    if isinstance(field, serializers.ListSerializer):
        return APISchema(type="array", items=map_serializer(field.child))

    if isinstance(field, serializers.Serializer):
        return map_serializer(field)

    if isinstance(field, serializers.ChoiceField):
        choices = list(dict.fromkeys(field.choices))
        type_: Optional[APIType] = None

        if all(isinstance(choice, bool) for choice in choices):
            type_ = "boolean"
        elif all(isinstance(choice, int) for choice in choices):
            type_ = "integer"
        elif all(isinstance(choice, (int, float, Decimal)) for choice in choices):
            type_ = "number"
        elif all(isinstance(choice, str) for choice in choices):
            type_ = "string"

        mapping = APISchema(enum=choices)
        if type_ is not None:
            mapping["type"] = type_

        if isinstance(field, serializers.MultipleChoiceField):
            return APISchema(type="array", items=mapping)
        return mapping

    if isinstance(field, serializers.ListField):
        mapping = APISchema(type="array", items={})
        if not isinstance(field.child, _UnvalidatedField):
            mapping["items"] = map_field(field.child)
        return mapping

    if isinstance(field, serializers.DateField):
        return APISchema(type="string", format="date")

    if isinstance(field, serializers.DateTimeField):
        return APISchema(type="string", format="date-time")

    if isinstance(field, serializers.EmailField):
        return APISchema(type="string", format="email")

    if isinstance(field, serializers.URLField):
        return APISchema(type="string", format="uri")

    if isinstance(field, serializers.UUIDField):
        return APISchema(type="string", format="uuid")

    if isinstance(field, serializers.IPAddressField):
        content = APISchema(type="string")
        if field.protocol != "both":
            content["format"] = field.protocol  # type: ignore
        return content

    if isinstance(field, serializers.DecimalField):
        if getattr(field, "coerce_to_string", api_settings.COERCE_DECIMAL_TO_STRING):
            content = APISchema(type="string", format="decimal")
        else:
            content = APISchema(type="number")

        if field.decimal_places:
            content["multipleOf"] = float("." + (field.decimal_places - 1) * "0" + "1")
        if field.max_whole_digits:
            content["maximum"] = int(field.max_whole_digits * "9") + 1
            content["minimum"] = -content["maximum"]
        if field.max_value:
            content["maximum"] = field.max_value
        if field.min_value:
            content["minimum"] = field.min_value

        return content

    if isinstance(field, serializers.FloatField):
        content = APISchema(type="number")
        if field.max_value:
            content["maximum"] = field.max_value
        if field.min_value:
            content["minimum"] = field.min_value
        return content

    if isinstance(field, serializers.IntegerField):
        content = APISchema(type="integer")
        if field.max_value:
            content["maximum"] = field.max_value
            if field.max_value > 2_147_483_647:
                content["format"] = "int64"
        if field.min_value:
            content["minimum"] = field.min_value
            if field.min_value > 2_147_483_647:
                content["format"] = "int64"
        return content

    if isinstance(field, serializers.FileField):
        return APISchema(type="string", format="binary")

    if isinstance(field, serializers.BooleanField):
        return APISchema(type="boolean")

    if isinstance(field, serializers.JSONField):
        return APISchema(type="object")

    if isinstance(field, serializers.DictField):
        return APISchema(type="object")

    if isinstance(field, serializers.HStoreField):
        return APISchema(type="object")

    return APISchema(type="string")


def map_serializer(serializer: SerializerOrSerializerType) -> APISchema:  # pylint: disable=too-many-branches
    required = []
    result = APISchema(type="object", properties={})

    if is_serializer_class(serializer):
        serializer = serializer(many=getattr(serializer, "many", False))

    if isinstance(serializer, serializers.ListSerializer):
        return APISchema(type="array", items=map_serializer(getattr(serializer, "child", serializer)))

    for field in serializer.fields.values():  # pragma: no cover
        if isinstance(field, serializers.HiddenField):
            continue

        if field.required:
            required.append(field.field_name)

        schema = map_field(field)

        if field.read_only:
            schema["readOnly"] = True
        if field.write_only:
            schema["writeOnly"] = True
        if field.allow_null:
            schema["nullable"] = True
        if field.default is not None and field.default != empty and not callable(field.default):
            schema["default"] = field.default
        if field.help_text:
            schema["description"] = str(field.help_text)

        map_field_validators(field, schema)

        result["properties"][field.field_name] = schema

    if required:
        result["required"] = required

    return result


def map_field_validators(field: serializers.Field, schema: APISchema) -> None:  # pragma: no cover
    for validator in field.validators:
        if isinstance(validator, validators.EmailValidator):
            schema["format"] = "email"

        if isinstance(validator, validators.URLValidator):
            schema["format"] = "uri"

        if isinstance(validator, validators.RegexValidator):
            schema["pattern"] = validator.regex.pattern.replace("\\Z", "\\z")

        elif isinstance(validator, validators.MaxLengthValidator):
            attr_name = "maxItems" if isinstance(field, serializers.ListField) else "maxLength"
            schema[attr_name] = validator.limit_value

        elif isinstance(validator, validators.MinLengthValidator):
            attr_name = "minItems" if isinstance(field, serializers.ListField) else "minLength"
            schema[attr_name] = validator.limit_value

        elif isinstance(validator, validators.MaxValueValidator):
            schema["maximum"] = validator.limit_value

        elif isinstance(validator, validators.MinValueValidator):
            schema["minimum"] = validator.limit_value

        elif isinstance(validator, validators.DecimalValidator) and not getattr(
            field, "coerce_to_string", api_settings.COERCE_DECIMAL_TO_STRING
        ):
            if validator.decimal_places:
                schema["multipleOf"] = float("." + (validator.decimal_places - 1) * "0" + "1")
            if validator.max_digits:
                digits = validator.max_digits
                if validator.decimal_places is not None and validator.decimal_places > 0:
                    digits -= validator.decimal_places
                schema["maximum"] = int(digits * "9") + 1
                schema["minimum"] = -schema["maximum"]


class PipelineSchema(ViewInspector):  # pylint: disable=too-many-instance-attributes,too-many-public-methods

    view: "BasePipelineView"

    def __init__(
        self,
        *,
        responses: Optional[Dict[HTTPMethod, Dict[int, Union[str, Type[serializers.BaseSerializer]]]]] = None,
        callbacks: Optional[Dict[str, Dict[str, Dict[HTTPMethod, SchemaCallbackData]]]] = None,
        links: Optional[Dict[HTTPMethod, Dict[int, Dict[str, APILinks]]]] = None,
        query_parameters: Optional[Dict[HTTPMethod, List[str]]] = None,
        header_parameters: Optional[Dict[HTTPMethod, List[str]]] = None,
        cookie_parameters: Optional[Dict[HTTPMethod, List[str]]] = None,
        deprecated: Optional[List[HTTPMethod]] = None,
        security: Optional[Dict[HTTPMethod, Dict[str, List[str]]]] = None,
        external_docs: Optional[Dict[HTTPMethod, APIExternalDocumentation]] = None,
        public: Optional[Dict[HTTPMethod, bool]] = None,
        prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        operation_id_base: Optional[str] = None,
    ):
        """Create an OpenAPI 3.1 schema for a PipelineView.

        :param responses: Additional responses given in the endpoints.
        :param callbacks: Asynchronous, out-of-band requests that are made during the pipeline.
                          https://swagger.io/docs/specification/callbacks/
        :param links: Describes how the endpoints relate to other endpoints.
                      https://swagger.io/docs/specification/links/
        :param query_parameters: Which parameters in the input serializer are query parameters?
        :param header_parameters: Which parameters in the input serializer are header parameters?
        :param cookie_parameters: Which parameters in the input serializer are cookie parameters?
        :param deprecated: Is this endpoint deprecated?
        :param security: Which security schemes the endpoints use.
        :param external_docs: External docs for the endpoints.
        :param public: Is the endpoint public or not?
        :param prefix: Prefix to remove from the tags.
        :param tags: User-defined tags for the endpoint. If not set, will be deducted from the path.
        :param operation_id_base: User-defined operation ID for the endpoint.
                                  If not set, it will be deducted from the input serializer.
        """
        self.responses = responses or {}
        self.callbacks = callbacks or {}
        self.links = links or {}
        self.query_parameters = query_parameters or {}
        self.header_parameters = header_parameters or {}
        self.cookie_parameters = cookie_parameters or {}
        self.deprecated = deprecated or {}
        self.security = security or {}
        self.external_docs = external_docs or {}
        self.public = public or {}
        self.prefix = prefix or ""
        self.operation_id_base = operation_id_base
        self.tags = tags
        super().__init__()

    def get_description(self, path: str, method: HTTPMethod) -> str:
        serializer_class = self.view.get_serializer_class()
        description = serializer_class.__doc__ or (self.view.__class__.__doc__ or "")
        return self._get_description_section(self.view, method, formatting.dedent(smart_str(description)))

    def get_operation_id(self, path: str, method: HTTPMethod) -> str:
        method_mapping = {
            "GET": "retrieve",
            "POST": "create",
            "PUT": "update",
            "PATCH": "partialUpdate",
            "DELETE": "destroy",
        }

        action = "list"
        if not getattr(self.view.get_serializer_class(output=True), "many", False):
            action = method_mapping.get(method) or snake_case_to_camel_case(method.lower())

        if self.operation_id_base is not None:
            return action + self.operation_id_base

        serializer_class_name = self.view.get_serializer_class().__name__
        operation_id_base = serializer_pattern.sub("", serializer_class_name)

        if operation_id_base == "":
            raise ValueError(  # pragma: no cover
                f'"{serializer_class_name}" is an invalid class name for schema generation. '
                f'Serializer\'s class name should be unique and explicit. e.g., "ItemSerializer"'
            )

        return action + operation_id_base

    def get_operation(self, path: str, method: HTTPMethod) -> APIOperation:
        operation: APIOperation = {}

        operation["operationId"] = self.get_operation_id(path, method)
        operation["description"] = self.get_description(path, method)

        operation["parameters"] = self.get_parameters(path, method)

        request_body = self.get_request_body(path, method)
        if request_body:
            operation["requestBody"] = request_body

        callbacks = self.get_callbacks(path, method)
        if callbacks:
            operation["callbacks"] = callbacks

        operation["responses"] = self.get_responses(path, method)
        operation["tags"] = self.get_tags(path, method)

        if method in self.deprecated:
            operation["deprecated"] = True

        security = self.security.get(method)
        if security is not None:
            operation["security"] = [security]

        external_docs = self.external_docs.get(method)
        if external_docs is not None:
            operation["externalDocs"] = external_docs

        return operation

    def get_component_name(self, serializer: SerializerOrSerializerType) -> str:
        if isinstance(serializer, serializers.ListSerializer):
            serializer = getattr(serializer, "child", serializer)

        if not is_serializer_class(serializer):
            serializer = serializer.__class__

        serializer_class_name = serializer.__name__
        component_name = serializer_pattern.sub("", serializer_class_name)

        if component_name == "":
            raise ValueError(  # pragma: no cover
                f"{serializer_class_name!r} is an invalid class name for schema generation. "
                f"Serializer's class name should be unique and explicit. e.g., 'ItemSerializer'"
            )

        return component_name

    def get_components(self, path: str, method: HTTPMethod) -> Dict[str, APISchema]:
        components: Dict[str, APISchema] = {}

        request_serializer_class = self.view.get_serializer_class()
        response_serializer_class = self.view.get_serializer_class(output=True)

        for serializer_class in (request_serializer_class, response_serializer_class):
            serializer = self.view.initialize_serializer(serializer_class=serializer_class)
            content = map_serializer(serializer)
            component_name = self.get_component_name(serializer)
            components.setdefault(component_name, content)

        for method_responses in self.responses.values():
            for serializer_class in method_responses.values():
                if not is_serializer_class(serializer_class):
                    continue

                serializer = self.view.initialize_serializer(serializer_class=serializer_class)
                content = map_serializer(serializer)
                component_name = self.get_component_name(serializer)
                components.setdefault(component_name, content)

        return components

    def get_callbacks(self, path: str, method: HTTPMethod) -> Dict[str, Dict[str, APIPathItem]]:
        if not self.callbacks:
            return {}

        callback_data = {}

        for event, callbacks in self.callbacks.items():
            callback_data.setdefault(event, {})
            for callback_url, methods in callbacks.items():
                callback_data[event].setdefault(callback_url, {})
                for method_name, data in methods.items():
                    callback_data[event][callback_url].setdefault(method_name.lower(), {})

                    request_body = data["request_body"]
                    if not is_serializer_class(request_body):
                        request_body = serializer_from_callable(request_body)

                    callback_data[event][callback_url][method_name.lower()]["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": map_serializer(request_body),
                            },
                        },
                    }

                    output_serializers = {}
                    for status_code, response in data["responses"].items():
                        if not is_serializer_class(response):
                            response = serializer_from_callable(response)

                        output_serializers[status_code] = {
                            "content": {
                                "application/json": {
                                    "schema": map_serializer(response),
                                },
                            },
                        }

                    callback_data[event][callback_url][method_name.lower()]["responses"] = output_serializers

        return callback_data

    def get_parameters(self, path: str, method: HTTPMethod) -> List[APIParameter]:  # pylint: disable=R0912
        serializer = self.view.get_serializer()
        if isinstance(serializer, serializers.ListSerializer):
            serializer = getattr(serializer, "child", serializer)

        parameters: List[APIParameter] = []
        path_parameters = list(get_path_parameters(path))
        query_parameters = self.query_parameters.get(method, [])
        header_parameters = self.header_parameters.get(method, [])
        cookie_parameters = self.cookie_parameters.get(method, [])

        if isinstance(serializer, HeaderAndCookieSerializer):
            for header_name in serializer.take_from_headers:
                if header_name not in header_parameters:
                    header_parameters.append(header_name)

            for cookie_name in serializer.take_from_cookies:
                if cookie_name not in cookie_parameters:
                    cookie_parameters.append(cookie_name)

        for field_name, field in serializer.fields.items():
            parameter = APIParameter(
                name=field_name,
                required=field.required,
                description=str(field.help_text) if field.help_text is not None else "",
                schema=map_field(field),
            )

            if field_name in path_parameters:
                parameter["in"] = "path"
                parameter["required"] = True
            elif field_name in query_parameters:
                parameter["in"] = "query"
            elif field_name in header_parameters:
                parameter["in"] = "header"
            elif field_name in cookie_parameters:
                parameter["in"] = "cookie"
            elif method == "GET":
                parameter["in"] = "query"
            else:
                continue

            parameters.append(parameter)

        return parameters

    def get_parsers(self) -> List[str]:
        return [parser_class.media_type for parser_class in self.view.parser_classes]

    def get_renderers(self) -> List[str]:
        return [
            renderer.media_type
            for renderer in self.view.renderer_classes
            if not issubclass(renderer, BrowsableAPIRenderer)
        ]

    def get_reference(self, serializer: serializers.Serializer) -> Dict[Literal["schema"], APISchema]:
        if isinstance(serializer, MockSerializer):
            if serializer.fields:
                return {"schema": map_serializer(serializer)}
            return {"schema": convert_to_schema(serializer._example)}  # pylint: disable=protected-access

        if isinstance(serializer, EmptySerializer):
            return self.get_no_result_schema()

        if isinstance(serializer, serializers.ListSerializer):
            return {
                "schema": APISchema(
                    type="array",
                    items={
                        "$ref": (
                            f"#/components/schemas/"
                            f"{self.get_component_name(getattr(serializer, 'child', serializer))}"
                        )
                    },
                ),
            }

        return APISchema(
            schema={
                "$ref": f"#/components/schemas/{self.get_component_name(serializer)}",
            },
        )

    def get_tags(self, path: str, method: HTTPMethod) -> List[str]:
        if self.tags:
            return self.tags

        if path.startswith("/"):
            path = path[1:]

        if path.startswith(self.prefix):
            path = path[len(self.prefix) :]

        return [path.split("/")[0].replace("_", "-")]

    def get_request_body(self, path: str, method: HTTPMethod) -> APIRequestBody:
        if method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return {}

        input_serializer = self.view.get_serializer()

        params: Set[str] = {param["name"] for param in self.get_parameters(path, method)}

        if params:
            is_list_serializer = isinstance(input_serializer, serializers.ListSerializer)
            child_serializer = getattr(input_serializer, "child", input_serializer)

            fields = {key: value for key, value in child_serializer.fields.items() if key not in params}
            new_serializer_class = type(input_serializer.__class__.__name__, (MockSerializer,), fields)
            if is_list_serializer:
                new_serializer_class.many = True  # pragma: no cover

            new_serializer_class.__doc__ = input_serializer.__class__.__doc__
            input_serializer = self.view.initialize_serializer(serializer_class=new_serializer_class)

        item_schema = self.get_reference(input_serializer)

        if not item_schema["schema"].get("properties", True):
            return {}  # pragma: no cover

        return {
            "content": {content_type: item_schema for content_type in self.get_parsers()},
        }

    def get_responses(self, path: str, method: HTTPMethod) -> APIResponses:
        data = APIResponses()

        responses = self.responses.get(method, {})
        if not responses and method not in self.view.pipelines:
            return data

        method_links = self.links.get(method, {})
        authentication_classes = self.view.authentication_classes
        permission_classes = self.view.permission_classes

        if ... not in set(responses.values()):
            responses.setdefault(200, ...)

        if authentication_classes:
            responses.setdefault(401, "Unauthenticated.")

        if permission_classes and permission_classes != [AllowAny]:
            responses.setdefault(403, "Permission Denied.")

        for status_code, info in responses.items():
            serializer_class: Optional[SerializerType] = None

            if info is ...:
                serializer_class = self.view.get_serializer_class(output=True)
                info = serializer_class.__doc__ or ""

                if getattr(serializer_class, "many", False):
                    data.setdefault("204", self.get_no_result_schema())

            elif is_serializer_class(info):
                serializer_class = info
                info = serializer_class.__doc__ or ""

            if serializer_class is not None:
                serializer = self.view.initialize_serializer(serializer_class=serializer_class)

                if isinstance(serializer, EmptySerializer):
                    status_code = 204

                response_schema = self.get_reference(serializer)
            else:
                response_schema = {"schema": self.get_error_message_schema()}

            data[str(status_code)] = {
                "content": {content_type: response_schema for content_type in self.get_renderers()},
                "description": info,
            }

            links = method_links.get(status_code, None)
            if links is not None:
                data[str(status_code)]["links"] = links

        return data

    def get_no_result_schema(self, description: str = "no results") -> APIParameter:
        return APIParameter(
            content={"application/json": APISchema(type="string", default="")},
            description=description,
        )

    def get_error_message_schema(self, error_message: str = "error message") -> APISchema:
        return APISchema(
            type="object",
            properties={"detail": APISchema(type="string", default=error_message)},
        )


class PipelineEndpointEnumerator(EndpointEnumerator):

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


class PipelineSchemaGenerator(BaseSchemaGenerator):

    openapi: Literal["3.0.2"] = "3.0.2"
    webhooks: Dict[str, SchemaWebhook] = {}
    contact: APIContact = {}
    license: APILicense = {}
    terms_of_service: str = ""
    public: bool = True
    security_schemes: Dict[str, APISecurityScheme] = {}
    security_rules: SecurityRules = {}

    endpoint_inspector_cls = PipelineEndpointEnumerator

    def __init__(
        self,
        *,
        title: Optional[str] = None,
        url: Optional[str] = None,
        description: Optional[str] = None,
        patterns: Optional[List[str]] = None,
        urlconf: Optional[str] = None,
        version: Optional[str] = None,
        webhooks: Optional[Dict[str, SchemaWebhook]] = None,
        contact: Optional[APIContact] = None,
        license: Optional[APILicense] = None,  # pylint: disable=redefined-builtin
        terms_of_service: Optional[str] = None,
        public: Optional[bool] = None,
        security_schemes: Optional[Dict[str, APISecurityScheme]] = None,
        security_rules: Optional[SecurityRules] = None,
    ):
        """Custom Schema Generator for Pipeline Views.

        :param title: The name of the API (required).
        :param url: The root URL of the API schema. This option is not required unless
                    the schema is included under path prefix.
        :param description: Longer descriptive text.
        :param patterns: A list of URLs to inspect when generating the schema.
                         Defaults to the project's URL conf.
        :param urlconf: A URL conf module name to use when generating the schema.
                        Defaults to settings.ROOT_URLCONF.
        :param version: The version of the API. Defaults to 0.1.0.
        :param webhooks: Webhooks defined in the API.
        :param contact: API developer contact information.
        :param license: API license information.
        :param terms_of_service: API terms of service link.
        :param public: If False, hide endpoint schema if the user does not have permissions to view it.
        :param security_schemes: Mapping of security scheme name to its definition.
        :param security_rules: Security schemes to apply if defined authentication or
                               permission class(es) exist on an endpoint.
        """
        if url and not url.startswith("/"):
            url = f"/{url}"

        super().__init__(
            title=title,
            url=url,
            description=description,
            patterns=patterns,
            urlconf=urlconf,
            version=version,
        )

        self.webhooks = webhooks or self.webhooks
        self.endpoint_inspector_cls.url = self.url or ""
        self.contact = contact or self.contact
        self.license = license or self.license
        self.terms_of_service = terms_of_service or self.terms_of_service
        self.public = public if public is not None else self.public
        self.security_schemes = security_schemes or self.security_schemes
        self.security_rules = security_rules or self.security_rules

    @classmethod
    def configure(
        cls,
        *,
        webhooks: Optional[Dict[str, SchemaWebhook]] = None,
        contact: Optional[APIContact] = None,
        license: Optional[APILicense] = None,  # pylint: disable=redefined-builtin
        terms_of_service: Optional[str] = None,
        public: Optional[bool] = None,
        security_schemes: Optional[Dict[str, APISecurityScheme]] = None,
        security_rules: Optional[SecurityRules] = None,
    ) -> Type[PipelineSchemaGenerator]:
        """Configure API with additional options

        :param webhooks: Webhooks defined in the API.
        :param contact: API developer contact information.
        :param license: API license information.
        :param terms_of_service: API terms of service link.
        :param public: If False, hide endpoint schema if the user does not have permissions to view it.
        :param security_schemes: Mapping of security scheme name to its definition.
        :param security_rules: Security schemes to apply if defined authentication or
                               permission class(es) exist on an endpoint.
        :return: New subclass with the added options.
        """
        return type(  # type: ignore
            cls.__name__,
            (cls,),
            {
                "webhooks": webhooks or cls.webhooks,
                "contact": contact or {},
                "license": license or cls.license,
                "terms_of_service": terms_of_service or cls.terms_of_service,
                "public": public if public is not None else cls.public,
                "security_schemes": security_schemes or cls.security_schemes,
                "security_rules": security_rules or cls.security_rules,
            },
        )

    def get_info(self) -> APIInfo:
        info = APIInfo(
            title=self.title or "",
            version=self.version or "",
        )
        if self.description is not None:
            info["description"] = self.description
        if self.contact:
            info["contact"] = self.contact
        if self.license:
            info["license"] = self.license
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service
        return info

    def get_normalized_path(self, path: str) -> str:
        if path.startswith("/"):
            path = path[1:]  # pragma: no cover
        return urljoin(self.url or "/", path)

    def get_schema(self, request: Optional[Request] = None, public: bool = False) -> OpenAPI:  # pylint: disable=R0914
        schema = OpenAPI(
            openapi=self.openapi,
            info=self.get_info(),
        )

        self._initialise_endpoints()
        operation_ids: Dict[str, PathAndMethod] = {}

        view_endpoints: List[Tuple[str, HTTPMethod, "BasePipelineView"]]
        _, view_endpoints = self._get_paths_and_endpoints(None if public else request)

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue  # pragma: no cover

            new_operation = self.get_operation(path, method, view)
            if new_operation:
                path = self.get_normalized_path(path)
                self.check_operation_id(path, method, new_operation["operationId"], operation_ids)
                schema.setdefault("paths", {}).setdefault(path, {})
                schema["paths"][path][method.lower()] = new_operation

            new_components = self.get_components(path, method, view)
            if new_components:
                schema.setdefault("components", {}).setdefault("schemas", {})
                self.check_components(new_components, schema["components"]["schemas"])
                schema["components"]["schemas"].update(new_components)

        webhooks = self.get_webhook()
        if webhooks:
            schema.setdefault("webhooks", {})
            schema["webhooks"].update(webhooks)

        if self.security_schemes:
            schema.setdefault("components", {})
            schema["components"]["securitySchemes"] = self.security_schemes

        sorted_paths = {}
        for path, operations in schema["paths"].items():
            tag = list(operations.values())[0]["tags"][0]
            sorted_paths.setdefault(tag, {})
            sorted_paths[tag][path] = operations

        schema["paths"] = {
            path: operations
            for operations in dict(sorted(sorted_paths.items())).values()
            for path, operations in dict(sorted(operations.items())).items()
        }

        return schema

    def get_components(self, path: str, method: HTTPMethod, view: "BasePipelineView") -> Dict[str, APISchema]:
        return view.schema.get_components(path, method)

    def get_operation(self, path: str, method: HTTPMethod, view: "BasePipelineView") -> APIOperation:
        return view.schema.get_operation(path, method)

    def get_webhook(self) -> Dict[str, APIPathItem]:
        webhooks: Dict[str, APIPathItem] = {}

        for webhook_name, webhook in self.webhooks.items():
            input_serializer = webhook["request_data"](many=getattr(webhook["request_data"], "many", False))
            if isinstance(input_serializer, serializers.ListSerializer):  # pragma: no cover
                input_serializer = getattr(input_serializer, "child", input_serializer)

            webhooks[webhook_name] = {  # type: ignore
                webhook["method"]: APIOperation(
                    requestBody={
                        "description": input_serializer.__class__.__doc__ or "",
                        "content": {
                            "application/json": {
                                "schema": map_serializer(input_serializer),
                            },
                        },
                    },
                    responses={  # type: ignore
                        str(status_code): {
                            "description": response.__doc__ or "",
                            "content": {"application/json": map_serializer(response)},
                        }
                        if is_serializer_class(response)
                        else {"description": response or ""}
                        for status_code, response in webhook["responses"].items()
                    },
                ),
            }

        return webhooks

    def check_components(self, new_components: Dict[str, APISchema], old_components: Dict[str, APISchema]) -> None:
        for name, component in new_components.items():
            if name not in old_components:
                continue
            if component == old_components[name]:
                continue
            warnings.warn(f"Schema component {name!r} has been overriden with a different value.")  # pragma: no cover

    def check_operation_id(
        self,
        path: str,
        method: HTTPMethod,
        operation_id: str,
        operation_ids: Dict[str, PathAndMethod],
    ) -> None:
        if operation_id in operation_ids:
            warnings.warn(  # pragma: no cover
                f"""
                You have a duplicated operationId in your OpenAPI schema: {operation_id}
                    Route: {operation_ids[operation_id]["path"]}, Method: {operation_ids[operation_id]["method"]}
                    Route: {path}, Method: {method}
                An operationId has to be unique across your schema.
                Your schema may not work in other tools.
                """
            )
        operation_ids[operation_id] = PathAndMethod(path=path, method=method)

    def has_view_permissions(self, path: str, method: HTTPMethod, view: BasePipelineView) -> bool:
        self.set_security_schemes(method, view)

        method_public = getattr(view.schema, "public", {}).get(method, None)

        if method_public is True:
            return True

        if self.public and method_public is not False:
            return True

        return super().has_view_permissions(path, method, view)

    def set_security_schemes(self, method: HTTPMethod, view: BasePipelineView) -> None:
        security = getattr(view.schema, "security", None)
        if security is None:
            return  # pragma: no cover

        for classes, rules in self.security_rules.items():
            if not isinstance(classes, tuple):
                classes = (classes,)

            if any(cls in view.permission_classes or cls in view.authentication_classes for cls in classes):
                view.schema.security.setdefault(method, {})
                # View specific rules take higher priority
                view.schema.security[method] = {**rules, **view.schema.security[method]}
