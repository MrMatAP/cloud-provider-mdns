import typing
import asyncio

import kubernetes_asyncio as kubernetes # type: ignore

from cloud_provider_mdns.base import Gateway, GatewayListener, NSRecord, NSRecordUpdate


class GatewayRegistry:
    """
    Utility class for resources making use of the Gateway API to look up their reference.
    We could add caching to this, but it's somewhat dangerous since the gateway may have been
    modified since we last cached it. We could watch for Gateway changes, but there is no
    guarantee that we would capture the change before the resource using the Gateway. So for now,
    we'll just make an additional API call
    """

    def __init__(self, api: kubernetes.client.CustomObjectsApi):
        self._api = api

    # The obvious choice here would be to deserialise the IoK8sNetworkingGatewayV1Gateway model
    # but it fails to parse the IPAddresses in its inner status
    async def get_gtw(self, namespace: str, name: str) -> Gateway:
        """
        Query the Kubernetes API for a Gateway reference
        Args:
            namespace (): The namespace of the Gateway
            name (): The gateway name

        Returns:
            A Gateway object
        """
        gtw_raw = await self._api.get_namespaced_custom_object('gateway.networking.k8s.io',
                                                               'v1',
                                                               namespace,
                                                               'gateways',
                                                               name)
        gtw_addresses = gtw_raw.get('status', {}).get('addresses', {})
        gtw_listeners = gtw_raw.get('spec', {}).get('listeners', [])
        listeners = [GatewayListener(port=l.get('port'),
                                     protocol=l.get('protocol'),
                                     ip_addresses=[a.get('value') for a in gtw_addresses])
                     for l in gtw_listeners]
        return Gateway(namespace=namespace,
                       name=name,
                       listeners=listeners)


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
        return {rec for rec in self._records if rec.owned_by(namespace, name)}

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