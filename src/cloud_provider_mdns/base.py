import abc
import asyncio
import typing
import enum
import dataclasses
import logging


class NSUpdateType(enum.Enum):
    """
    An enumeration of update types
    """
    ADD = enum.auto()
    MODIFY = enum.auto()
    REMOVE = enum.auto()


@dataclasses.dataclass
class NSUpdate:
    """
    All required data to create, modify or remove a name service record
    """
    update: NSUpdateType
    name: str
    svc: str
    ip_addresses: typing.List[str] = dataclasses.field(default_factory=list)
    port: int = 80

    @property
    def svc_fqdn(self) -> str:
        return f'{self.name}.{self.svc}'

    @property
    def fqdn(self) -> str:
        return f'{self.name}.local'


class BaseTask:

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