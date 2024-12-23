import typing
import asyncio

import zeroconf
import zeroconf.asyncio

from base import BaseTask, NSUpdate, NSUpdateType


class ZeroConfNameserver(BaseTask):

    def __init__(self, q: asyncio.Queue):
        super().__init__()
        self._q = q
        self._aiozc = zeroconf.asyncio.AsyncZeroconf(ip_version=zeroconf.IPVersion.All)
        self._known: typing.Dict[str, zeroconf.ServiceInfo] = {}

    async def run(self):
        try:
            self._logger.info('Starting')
            while True:
                nr: NSUpdate = await self._q.get()
                match nr.update:
                    case NSUpdateType.REMOVE:
                        if nr.svc_fqdn not in self._known:
                            self._logger.warning(f'Service {nr.svc_fqdn} not found in known services')
                            continue
                        await self._aiozc.async_unregister_service(self._known[nr.svc_fqdn])
                        del self._known[nr.svc_fqdn]
                        self._logger.info(f'Unregistered {nr.fqdn}')
                    case NSUpdateType.MODIFY:
                        if nr.svc_fqdn not in self._known:
                            self._logger.warning(f'Service {nr.fqdn} not found in known services')
                            continue
                        self._known[nr.svc_fqdn] = zeroconf.ServiceInfo(
                            nr.svc,
                            nr.svc_fqdn,
                            port=nr.port,
                            addresses=nr.ip_addresses,
                            server=nr.fqdn)
                        await self._aiozc.async_update_service(self._known[nr.svc_fqdn])
                        self._logger.info(f'Modified {nr.fqdn}')
                    case NSUpdateType.ADD:
                        self._known[nr.svc_fqdn] = zeroconf.ServiceInfo(
                            nr.svc,
                            nr.svc_fqdn,
                            port=nr.port,
                            addresses=nr.ip_addresses,
                            server=nr.fqdn)
                        await self._aiozc.async_register_service(self._known[nr.svc_fqdn])
                        self._logger.info(f'Registered {nr.fqdn}')
        except asyncio.QueueShutDown:
            self._logger.info('Queue is shut down')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            raise
