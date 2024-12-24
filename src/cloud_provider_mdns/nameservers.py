import typing
import asyncio

import zeroconf
import zeroconf.asyncio

from cloud_provider_mdns.base import BaseTask, NSRecord, NSRecordUpdate
from cloud_provider_mdns.registries import RecordRegistry


class ZeroConfNameserver(BaseTask):

    def __init__(self, record_registry: RecordRegistry):
        super().__init__()
        self._record_registry = record_registry
        self._aiozc = zeroconf.asyncio.AsyncZeroconf(ip_version=zeroconf.IPVersion.All)
        self._registered: typing.Dict[str, zeroconf.ServiceInfo] = {}

    async def run(self):
        try:
            self._logger.info('Starting')
            q = self._record_registry.subscribe(self.__class__.__name__)
            while True:
                rec = await q.get()
                match rec.action:
                    case NSRecordUpdate.ADD:
                        if not rec.ns_fqdn.endswith('.local.'):
                            self._logger.warning(f'Ignoring registration as {rec.fqdn} does not '
                                              f'end with .local')
                            continue
                        try:
                            si = zeroconf.ServiceInfo(
                                f'{rec.svc}.local.',
                                rec.svc_fqdn,
                                port=rec.port,          # Port is required by Apple, apparently
                                addresses=rec.ip_addresses,
                                server=rec.ns_fqdn)
                            await self._aiozc.async_register_service(si)
                            self._registered[rec.ns_fqdn] = si
                            self._logger.info(f'Added {rec.ns_fqdn}')
                        except zeroconf.BadTypeInNameException:
                            self._logger.warning(f'Ignoring registration for {rec.fqdn} as it uses '
                                                 f'a bad name')
                    case NSRecordUpdate.MODIFY:
                        if rec.ns_fqdn not in self._registered:
                            self._logger.warning(f'Ignoring update as {rec.ns_fqdn} has not been '
                                                 f'registered previously')
                            continue
                        self._registered[rec.ns_fqdn].port = rec.port
                        self._registered[rec.ns_fqdn].addresses = rec.ip_addresses
                        await self._aiozc.async_update_service(self._registered[rec.ns_fqdn])
                        self._logger.info(f'Modified {rec.ns_fqdn}')
                    case NSRecordUpdate.REMOVE:
                        if rec.ns_fqdn not in self._registered:
                            self._logger.warning(f'Ignoring update as {rec.ns_fqdn} has not been '
                                                 f'registered previously')
                            continue
                        await self._aiozc.async_unregister_service(self._registered[rec.ns_fqdn])
                        del self._registered[rec.ns_fqdn]
                        self._logger.info(f'Removed {rec.ns_fqdn}')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            await self._aiozc.async_unregister_all_services()
            await self._aiozc.async_close()
            raise
