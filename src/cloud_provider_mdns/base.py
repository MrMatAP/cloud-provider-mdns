import abc
import asyncio
import enum
import typing
import dataclasses
import logging

import kubernetes_asyncio as kubernetes     # type: ignore[import-untyped]
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

class KubernetesGatewaySpec(PydanticIgnoreExtraFields):
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

class KubernetesGatewayStatus(PydanticIgnoreExtraFields):
    """
    Status for a Gateway
    """
    addresses: typing.List[GatewayAddresses] = pydantic.Field(default_factory=list)

class KubernetesGateway(PydanticIgnoreExtraFields):
    """
    A record for a Gateway
    """
    apiVersion: str = pydantic.Field(default='gateway.networking.k8s.io/v1')
    kind: str = pydantic.Field(default='Gateway')
    metadata: ObjectMeta
    spec: KubernetesGatewaySpec
    status: KubernetesGatewayStatus

    def addresses(self) -> typing.List[str]:
        """
        Get the IP addresses for the Gateway
        """
        return [address.value for address in self.status.addresses
                if address.type == 'IPAddress' and address.value is not None]

    def listens_on_port(self, port: int) -> bool:
        """
        Check if the Gateway listens on the specified port
        """
        return any(listener.port == port for listener in self.spec.listeners)

    def port_by_section_name(self, section_name: str) -> int | None:
        """
        Return the port for a given section name
        """
        section = list(filter(lambda s: s.name == section_name, self.spec.listeners))
        if len(section) == 0:
            return None
        return section[0].port

    def __str__(self) -> str:
        return f'{self.metadata.namespace}/{self.metadata.name}'

class VirtualServiceSpec(PydanticIgnoreExtraFields):
    """
    Virtual Service Spec
    """
    gateways: typing.List[str] = pydantic.Field(default_factory=list)
    hosts: typing.List[str] = pydantic.Field(default_factory=list)

class VirtualService(PydanticIgnoreExtraFields):
    """
    A record for a VirtualService
    """
    apiVersion: str = pydantic.Field(default='networking.istio.io/v1')
    kind: str = pydantic.Field(default='VirtualService')
    metadata: ObjectMeta
    spec: VirtualServiceSpec

class NativeIstioGatewaySpec(PydanticIgnoreExtraFields):
    """
    A record for the native Istio Gateway spec
    """
    selector: typing.Dict[str, str] = pydantic.Field(default_factory=dict)

class NativeIstioGateway(PydanticIgnoreExtraFields):
    """
    A record for a native Istio Gateway
    """
    apiVersion: str = pydantic.Field(default='networking.istio.io/v1')
    kind: str = pydantic.Field(default='Gateway')
    metadata: ObjectMeta
    spec: NativeIstioGatewaySpec



@dataclasses.dataclass(frozen=True)
class Record:
    """
    A record we maintain in multicast and/or unicast DNS
    """
    owner_id: str
    hostname: str
    ip_address: str
    gateway_id: str = dataclasses.field(default='0.0.0.0')
    port: int = dataclasses.field(default=80)

    @property
    def unqualified(self):
        """
        Return the unqualified hostname without its domain
        """
        return self.hostname.replace(f'.{self.domain}','')

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

    def __init__(self, registry: 'Registry', *args, **kwargs) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._registry = registry
        self._registry.subscribe(self)

    async def shutdown(self):
        pass

    async def update(self, records: typing.Set[Record]):
        pass

    async def add(self, rec: Record):
        raise NotImplementedError()

    async def modify(self, rec: Record):
        raise NotImplementedError()

    async def remove(self, rec: Record):
        raise NotImplementedError()

class BaseWatcher(BaseTask):

    def __init__(self, registry: 'Registry') -> None:
        super().__init__()
        self._registry = registry
        self._watch = kubernetes.watch.Watch()

    async def run(self):
        raise NotImplementedError

    async def register_record(self, op: str, record: Record):
        match op:
            case 'ADDED':
                await self._registry.add_record(record)
                self._logger.info(f'Record {record.owner_id} adds {record.hostname}')
            case 'MODIFIED':
                await self._registry.modify_record(record)
                self._logger.info(f'Record {record.owner_id} modifies {record.hostname}')
            case 'DELETED':
                await self._registry.remove_record(record)
                self._logger.info(f'Record {record.owner_id} removes {record.hostname}')

    @staticmethod
    async def _has_api(required_api_name: str) -> bool:
        """
        Return true when the cluster is aware of the provided API
        """
        apis_api = kubernetes.client.ApisApi()
        resources = await apis_api.get_api_versions()
        return list(filter(lambda r: r.name == required_api_name, resources.groups)) != []
