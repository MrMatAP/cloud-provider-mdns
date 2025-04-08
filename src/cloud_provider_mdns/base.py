import abc
import enum
import asyncio
import typing
import dataclasses
import logging

import pydantic

class PydanticIgnoreExtraFields(pydantic.BaseModel):
    """
    A base class for Pydantic models that ignores extra fields
    """
    class Config:
        extra = 'ignore'

class ResourceMetadata(PydanticIgnoreExtraFields):
    """
    Metadata for a HTTPRoute
    """
    name: str
    namespace: str

class HTTPRouteSpec(PydanticIgnoreExtraFields):
    """
    Spec for a HTTPRoute
    """
    hostnames: typing.List[str] = pydantic.Field(default_factory=list)

class HTTPRouteParentRef(PydanticIgnoreExtraFields):
    """
    ParentRef for a HTTPRoute
    """
    group: str | None = None
    kind: str
    name: str
    namespace: str | None = None
    sectionName: str | None = None

class HTTPRouteStatusCondition(PydanticIgnoreExtraFields):
    """
    Status condition for a HTTPRoute
    """
    type: str
    status: bool
    reason: str | None = None
    message: str | None = None

class HTTPRouteStatusParent(PydanticIgnoreExtraFields):
    """
    Status for a HTTPRoute parent
    """
    conditions: typing.List[HTTPRouteStatusCondition] = pydantic.Field(default_factory=list)
    parentRef: HTTPRouteParentRef

class HTTPRouteStatus(PydanticIgnoreExtraFields):
    """
    Status for a HTTPRoute
    """
    parents: typing.List[HTTPRouteStatusParent] = pydantic.Field(default_factory=list)

class HTTPRoute(PydanticIgnoreExtraFields):
    """
    A record for a HTTPRoute
    """
    metadata: ResourceMetadata
    spec: HTTPRouteSpec
    status: HTTPRouteStatus

    def accepted(self) -> bool:
        if len(self.status.parents) == 0:
            return False
        return all(condition.status for condition in self.status.parents[0].conditions \
                   if condition.type == 'Accepted')

    def __str__(self) -> str:
        return f'{self.metadata.namespace}/{self.metadata.name}'

class GatewayListenerSpec(PydanticIgnoreExtraFields):
    """
    Spec for a GatewayListener
    """
    name: str
    port: int
    protocol: str

class GatewaySpec(PydanticIgnoreExtraFields):
    """
    Spec for a Gateway
    """
    listeners: typing.List[GatewayListenerSpec] = pydantic.Field(default_factory=list)

class GatewayAddresses(PydanticIgnoreExtraFields):
    """
    Addresses for a Gateway
    """
    type: str
    value: str | None = None

class GatewayStatus(PydanticIgnoreExtraFields):
    """
    Status for a Gateway
    """
    addresses: typing.List[GatewayAddresses] = pydantic.Field(default_factory=list)

class Gateway(PydanticIgnoreExtraFields):
    """
    A record for a Gateway
    """
    metadata: ResourceMetadata
    spec: GatewaySpec
    status: GatewayStatus

    def addresses(self) -> typing.List[str]:
        """
        Get the IP addresses for the Gateway
        """
        return [address.value for address in self.status.addresses \
                if address.type == 'IPAddress']

    def listener_by_section_name(self, section_name: str) -> GatewayListenerSpec | None:
        """
        Get the listener by section name
        """
        for listener in self.spec.listeners:
            if listener.name == section_name:
                return listener
        return None

    def __str__(self) -> str:
        return f'{self.metadata.namespace}/{self.metadata.name}'

class NSRecordUpdate(enum.Enum):
    ADD = enum.auto()
    MODIFY = enum.auto()
    REMOVE = enum.auto()

@dataclasses.dataclass
class NSAddressPort:
    port: int
    ip_addresses: typing.List[str] = dataclasses.field(default_factory=list)

@dataclasses.dataclass(unsafe_hash=True)
class NSRecord:
    namespace: str
    name: str
    hostname: str
    action: NSRecordUpdate | None = dataclasses.field(default=None, hash=False)
    address_ports: typing.List[NSAddressPort] = dataclasses.field(default_factory=list, hash=False)

    @property
    def fqdn(self) -> str:
        return self.hostname if self.hostname.endswith('.') else f'{self.hostname}.'

    def is_owner(self, namespace: str, name: str) -> bool:
        return self.namespace == namespace and self.name == name

    def __str__(self) -> str:
        return f'{self.namespace}/{self.name}'


class BaseTask(abc.ABC):
    """
    A re-usable abstract base class for tasks
    """

    def __init__(self, *args, **kwargs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._task = None
        self._should_stop = False

    def start(self):
        """
        Create the task implemented within the run method
        """
        self._task = asyncio.create_task(self.run())

    def cancel(self):
        """
        Cancel the task if it is currently running
        """
        if self._task:
            self._task.cancel()

    @abc.abstractmethod
    async def run(self):
        """
        The asynchronous run method performs lengthy tasks
        """
        pass


@dataclasses.dataclass()
class ResourceId:
    namespace: str
    name: str

    @staticmethod
    def from_resource(obj: dict) -> 'ResourceId':
        namespace = obj.get('metadata', {}).get('namespace', None)
        name = obj.get('metadata', {}).get('name', None)
        if namespace is None or name is None:
            raise UnidentifiableResourceException(code=400,
                                                  msg='The provided resource cannot be identified '
                                                      'since it has no namespace or name')
        return ResourceId(namespace=namespace, name=name)   # noqa

    @property
    def id(self) -> str:
        return f'{self.namespace}/{self.name}'

    def __str__(self) -> str:
        return self.id

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.namespace}, {self.name})'


class CPMException(Exception):
    """
    A custom base exception for cloud-provider-mdns
    """

    def __init__(self, code: int, msg: str):
        super().__init__()
        self._code = code
        self._msg = msg

    @property
    def code(self) -> int:
        return self._code

    @property
    def msg(self) -> str:
        return self._msg

    def __str__(self) -> str:
        return f'[{self._code}] {self._msg}'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._code}, {self._msg})'

class UnidentifiableResourceException(CPMException):
    """
    An exception raised when a Kubernetes resource has no namespace or name
    """
    pass

class GatewayNotReadyException(CPMException):
    """
    An exception raised when the Gateway for a HTTPRoute is not yet ready
    """
    pass
