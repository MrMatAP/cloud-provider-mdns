import abc
import enum
import asyncio
import typing
import dataclasses
import logging

class NSRecordUpdate(enum.Enum):
    ADD = enum.auto()
    MODIFY = enum.auto()
    REMOVE = enum.auto()

@dataclasses.dataclass(unsafe_hash=True)
class NSRecord:
    fqdn: str
    owner_namespace: str
    owner_name: str
    svc: str = '_http._tcp'
    ip_addresses: typing.List[str] = dataclasses.field(default_factory=list, hash=False)
    port: int = 80
    action: NSRecordUpdate | None = dataclasses.field(default=None, hash=False)

    @property
    def ns_fqdn(self) -> str:
        return self.fqdn if self.fqdn.endswith('.') else f'{self.fqdn}.'

    @property
    def svc_fqdn(self) -> str:
        labels = self.fqdn.split('.')
        hostname = '.'.join(labels[:1])
        return f'{hostname}.{self.svc}.{labels[-1]}.'

    def owned_by(self, namespace: str, name: str) -> bool:
        return self.owner_namespace == namespace and self.owner_name == name

    @property
    def auth_id(self) -> str:
        return f'{self.owner_namespace}/{self.owner_name}'


@dataclasses.dataclass
class GatewayListener:
    """
    All required data for a listener attached to a Kubernetes Gateway
    """
    port: int
    protocol: str
    ip_addresses: typing.List[str] = dataclasses.field(default_factory=list)

@dataclasses.dataclass
class Gateway:
    """
    All required data for a Kubernetes Gateway
    """
    name: str
    namespace: str
    listeners: typing.List[GatewayListener] = dataclasses.field(default_factory=list)


class BaseTask(abc.ABC):
    """
    A re-usable abstract base class for tasks
    """

    def __init__(self):
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
