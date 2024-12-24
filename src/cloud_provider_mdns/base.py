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