import abc
import enum
import asyncio
import typing
import dataclasses
import logging

import kubernetes_asyncio as kubernetes
import pydantic


class PydanticIgnoreExtraFields(pydantic.BaseModel):
    """
    A base class for Pydantic models that ignores extra fields
    """
    class Config:
        extra = 'ignore'

class ObjectMeta(PydanticIgnoreExtraFields):
    """
    Metadata for a HTTPRoute
    """
    name: str
    namespace: str

class ParentReference(PydanticIgnoreExtraFields):
    """
    ParentRef for a HTTPRoute
    """
    group: str = pydantic.Field(default='gateway.networking.k8s.io')
    kind: str = pydantic.Field(default='Gateway')
    namespace: str | None = None
    name: str
    sectionName: str | None = None
    port: int | None = None

class HTTPRouteSpec(PydanticIgnoreExtraFields):
    """
    Spec for a HTTPRoute.
    We omit the rules field since we do not need to parse it for registering DNS
    """
    parentRefs: typing.List[ParentReference] = pydantic.Field(default_factory=list)
    hostnames: typing.List[str] = pydantic.Field(default_factory=list)

class Condition(PydanticIgnoreExtraFields):
    """
    Status condition for a HTTPRoute
    We omit the reason and message fields as they are not relevant for registering DNS
    """
    type: str
    status: bool

class RouteParentStatus(PydanticIgnoreExtraFields):
    """
    Status for a HTTPRoute parent
    """
    parentRef: ParentReference
    controllerName: str
    conditions: typing.List[Condition] = pydantic.Field(default_factory=list)

class HTTPRouteStatus(PydanticIgnoreExtraFields):
    """
    Status for a HTTPRoute
    """
    parents: typing.List[RouteParentStatus] = pydantic.Field(default_factory=list)

class HTTPRoute(PydanticIgnoreExtraFields):
    """
    A record for a HTTPRoute
    """
    apiVersion: str = pydantic.Field(default='gateway.networking.k8s.io/v1')
    kind: str = pydantic.Field(default='HTTPRoute')
    metadata: ObjectMeta
    spec: HTTPRouteSpec
    status: HTTPRouteStatus

    def accepted(self) -> bool:
        if len(self.status.parents) == 0:
            return False
        return all(condition.status for condition in self.status.parents[0].conditions \
                   if condition.type == 'Accepted')

    def spec_parent_by_status_parent_ref(self, parent: RouteParentStatus) -> ParentReference:
        """
        Return the spec parent for the given status parent ref of the HTTPRoute
        """
        spec_parent = next((p for p in self.spec.parentRefs if p.name == parent.parentRef.name), None)
        if spec_parent is None:
            raise ValueError(f'No spec parent found for {parent.parentRef.name}')
        return spec_parent

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
    apiVersion: str = pydantic.Field(default='gateway.networking.k8s.io/v1')
    kind: str = pydantic.Field(default='Gateway')
    metadata: ObjectMeta
    spec: GatewaySpec
    status: GatewayStatus

    def addresses(self) -> typing.List[str]:
        """
        Get the IP addresses for the Gateway
        """
        return [address.value for address in self.status.addresses \
                if address.type == 'IPAddress']

    def listens_on_port(self, port: int) -> bool:
        """
        Check if the Gateway listens on the specified port
        """
        return any(listener.port == port for listener in self.spec.listeners)

    def port_by_section_name(self, section_name: str) -> int:
        """
        Return the port for a given section name
        """
        section = list(filter(lambda s: s.sectionName == section_name, self.spec.listeners))
        if len(section) == 0:
            raise ValueError(f'No section name found for {section_name}')
        return section[0].port

    def __str__(self) -> str:
        return f'{self.metadata.namespace}/{self.metadata.name}'


@dataclasses.dataclass(frozen=True)
class Record:
    """
    A record we maintain in multicast and/or unicast DNS
    """
    hostname: str
    ip_address: str
    port: int = dataclasses.field(default=443)

    @property
    def fqdn(self) -> str:
        """
        The fully qualified domain name
        """
        if self.hostname.endswith('.'):
            return self.hostname
        return f'{self.hostname}.'

    @property
    def domain(self) -> str:
        """
        The domain of the record
        """
        return self.hostname.split('.')[-1]


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


class BaseNameserver:
    """
    Common Nameserver implementation
    """

    def __init__(self, *args, **kwargs) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._records: typing.Set[Record] = ()

    async def shutdown(self):
        pass

    async def add(self, rec: Record):
        raise NotImplementedError()

    async def modify(self, rec: Record):
        raise NotImplementedError()

    async def remove(self, rec: Record):
        raise NotImplementedError()


class BaseWatcher(BaseTask):

    def __init__(self, nameservers: typing.Set[BaseNameserver]) -> None:
        super().__init__()
        self._nameservers: typing.Set[BaseNameserver] = nameservers or {}
        self._watch = kubernetes.watch.Watch()

    async def run(self):
        raise NotImplementedError

    async def add(self, event):
        raise NotImplementedError

    async def modify(self, event):
        raise NotImplementedError

    async def remove(self, event):
        raise NotImplementedError

    @staticmethod
    async def _has_api(required_api_name: str) -> bool:
        """
        Return true when the cluster is aware of the provided API
        """
        apis_api = kubernetes.client.ApisApi()
        resources = await apis_api.get_api_versions()
        return list(filter(lambda r: r.name == required_api_name, resources.groups)) != []
