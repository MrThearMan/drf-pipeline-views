from __future__ import annotations

from typing import _eval_type  # type: ignore
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Container,
    Coroutine,
    Dict,
    ForwardRef,
    Generator,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)


# New in version 3.8
try:
    from typing import Literal, Protocol, TypedDict
except ImportError:
    from typing_extensions import Literal, Protocol, TypedDict

# New in version 3.10
try:
    from typing import ParamSpec, TypeAlias
except ImportError:
    from typing_extensions import ParamSpec, TypeAlias


if TYPE_CHECKING:
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.permissions import BasePermission
    from rest_framework.request import Request
    from rest_framework.response import Response
    from rest_framework.serializers import BaseSerializer

    from .views import BasePipelineView  # pylint: disable=R0401


__all__ = [
    "HTTPMethod",
    "LogicCallable",
    "PipelineLogic",
    "PipelinesDict",
    "ViewContext",
    "TYPE_CHECKING",
    "Any",
    "Callable",
    "Dict",
    "List",
    "Tuple",
    "Iterable",
    "Literal",
    "Optional",
    "Type",
    "TypedDict",
    "Union",
    "Generator",
    "Protocol",
    "DataDict",
    "DataConditional",
    "DataReturn",
    "SerializerType",
    "TypesDict",
    "T",
    "P",
    "Set",
    "TypeAlias",
    "Container",
    "ForwardRef",
    "eval_type",
    "Coroutine",
    "ExternalDocs",
    "Sequence",
    "ViewMethod",
    "APIContact",
    "APILicense",
    "APIInfo",
    "APISchema",
    "BasicAuth",
    "BearerAuth",
    "ApiKeyAuth",
    "AnyAuth",
    "SecurityRules",
    "AuthOrPerm",
]


T = TypeVar("T")  # pylint: disable=C0103
P = ParamSpec("P")  # pylint: disable=C0103
eval_type = _eval_type
DataDict: TypeAlias = Dict[str, Any]
SerializerType: TypeAlias = Type["BaseSerializer"]
DataConditional: TypeAlias = Tuple[Any, DataDict]
DataReturn: TypeAlias = Union[DataDict, DataConditional, None]
HTTPMethod: TypeAlias = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
LogicCallable: TypeAlias = Callable[..., DataReturn]
PipelineLogic: TypeAlias = Union[LogicCallable, SerializerType, Iterable["PipelineLogic"]]  # type: ignore
PipelinesDict: TypeAlias = Dict[HTTPMethod, PipelineLogic]  # type: ignore
TypesDict: TypeAlias = Dict[str, Union[Optional[Type], "TypesDict"]]  # type: ignore
AuthOrPerm: TypeAlias = Union[Type["BasePermission"], Type["BaseAuthentication"]]
SecurityRules: TypeAlias = Dict[Union[Tuple[AuthOrPerm, ...], AuthOrPerm], Dict[str, List[str]]]


class ViewMethod(Protocol):
    def __call__(self: BasePipelineView, request: Request, *args: Any, **kwargs: Any) -> Response:
        """..."""


class ViewContext(TypedDict):
    request: Request
    format: str
    view: BasePipelineView


class ExternalDocs(TypedDict):
    description: str
    url: str


class APIContact(TypedDict, total=False):
    name: str
    url: str
    email: str


class APILicense(TypedDict, total=False):
    name: str
    url: str


class APIInfo(TypedDict, total=False):
    title: str
    version: str
    description: str
    contact: APIContact
    license: APILicense
    termsOfService: str


class APISchema(TypedDict, total=False):
    openapi: str
    info: APIInfo
    paths: Dict[str, Dict[str, Any]]
    components: Dict[str, Dict[str, Any]]
    security: List[Dict[str, List[Any]]]
    tags: List[Dict[str, Any]]
    externalDocs: ExternalDocs
    servers: List[Dict[str, Any]]


class BasicAuth(TypedDict):
    type: Literal["http"]
    scheme: Literal["basic"]


class BearerAuthBase(TypedDict):
    type: Literal["http"]
    scheme: Literal["bearer"]


class BearerAuth(BearerAuthBase, total=False):
    bearerFormat: str


ApiKeyAuth = TypedDict(
    "ApiKeyAuth",
    {
        "type": Literal["apiKey"],
        "in": Literal["header", "query", "cookie"],
        "name": str,
    },
)


class OAuthFlowBase(TypedDict):
    scopes: List[str]


class OAuthFlowAuthorizationCodeBase(OAuthFlowBase):
    authorizationUrl: str
    tokenUrl: str


class OAuthFlowAuthorizationCode(OAuthFlowAuthorizationCodeBase, total=False):
    refreshUrl: str


class OAuthFlowImplicitBase(OAuthFlowBase):
    authorizationUrl: str


class OAuthFlowImplicit(OAuthFlowImplicitBase, total=False):
    refreshUrl: str


class OAuthFlowPasswordBase(OAuthFlowBase):
    tokenUrl: str


class OAuthFlowPassword(OAuthFlowPasswordBase, total=False):
    refreshUrl: str


class OAuthFlowClientCredentialsBase(OAuthFlowBase):
    tokenUrl: str


class OAuthFlowClientCredentials(OAuthFlowClientCredentialsBase, total=False):
    refreshUrl: str


class OAuthFlows(TypedDict, total=False):
    authorizationCode: OAuthFlowAuthorizationCode
    implicit: OAuthFlowImplicit
    password: OAuthFlowPassword
    clientCredentials: OAuthFlowClientCredentials


class OAuthBase(TypedDict):
    type: Literal["openIdConnect"]
    flows: OAuthFlows


class OAuth(OAuthBase, total=False):
    description: str


class OpenIDAuth(TypedDict):
    type: Literal["oauth2"]
    openIdConnectUrl: str


AnyAuth: TypeAlias = Union[BasicAuth, BearerAuth, ApiKeyAuth, OAuth, OpenIDAuth]
