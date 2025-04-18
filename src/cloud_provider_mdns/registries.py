import typing
import asyncio

from cloud_provider_mdns.base import Record, NSRecord, NSRecordUpdate


class Records:
    def __init__(self):
        self._records: typing.List[Record] = []
        self._consumers: typing.Dict[str, asyncio.Queue] = {}

    async def add_record(self, record: Record):
        self._records.append(record)
        self._records.add(record)
        record.action = NSRecordUpdate.ADD
        await self._notify_all(record)

    async def modify_record(self, record: Record):
        self._records.add(record)
        record.action = NSRecordUpdate.MODIFY
        await self._notify_all(record)

    async def remove_record(self, record: Record):
        self._records.remove(record)
        record.action = NSRecordUpdate.REMOVE
        await self._notify_all(record)

    def subscribe(self, consumer: str) -> asyncio.Queue:
        """
        Subscribe to changes of the record registry
        Args:
            consumer (str): A unique identifier for the consumer

        Returns:
            A queue object to listen on for changes
        """
        self._consumers[consumer] = asyncio.Queue()
        return self._consumers[consumer]

    async def _notify_all(self, record: Record):
        """
        Notify all consumers of a change in the record registry
        Args:
            record (NSRecord): The record that has changed
        """
        for consumer in self._consumers.values():
            await consumer.put(record)


class RecordRegistry:

    def __init__(self) -> None:
        self._records: typing.Set[NSRecord] = set()
        self._consumers: typing.Dict[str, asyncio.Queue] = {}

    async def add_record(self, record: NSRecord):
        self._records.add(record)
        record.action = NSRecordUpdate.ADD
        await self._notify_all(record)

    async def modify_record(self, record: NSRecord):
        self._records.add(record)
        record.action = NSRecordUpdate.MODIFY
        await self._notify_all(record)

    async def remove_record(self, record: NSRecord):
        self._records.remove(record)
        record.action = NSRecordUpdate.REMOVE
        await self._notify_all(record)

    def by_fqdn(self, fqdn: str) -> typing.Optional[NSRecord]:
        """
        Return the record matching the provided fqdn or None if not found
        Args:
            fqdn (str): The FQDN to search for

        Returns:
            The NSRecord object matching the provided fqdn or None if not found
        """
        recs = filter(lambda rec: rec.fqdn == fqdn, self._records)
        return next(recs, None)

    def by_owner(self, namespace: str, name: str) -> typing.Set[NSRecord]:
        """
        Returns the records owned by the specified resource
        Args:
            namespace (str): The resource namespace
            name (str): The resource name

        Returns:
            A set of NSRecord objects known to be owned by the specified resource
        """
        return {rec for rec in self._records if rec.is_owner(namespace, name)}

    def subscribe(self, consumer: str) -> asyncio.Queue:
        """
        Subscribe to changes of the record registry
        Args:
            consumer (str): A unique identifier for the consumer

        Returns:
            A queue object to listen on for changes
        """
        self._consumers[consumer] = asyncio.Queue()
        return self._consumers[consumer]

    async def _notify_all(self, record: NSRecord):
        """
        Notify all consumers of a change in the record registry
        Args:
            record (NSRecord): The record that has changed
        """
        for consumer in self._consumers.values():
            await consumer.put(record)
