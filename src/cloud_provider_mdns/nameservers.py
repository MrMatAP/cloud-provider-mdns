import typing

import zeroconf
import zeroconf.asyncio
import dns.message
import dns.update
import dns.tsigkeyring
import dns.query
import dns.rcode
import dns.exception

from cloud_provider_mdns.base import Record, BaseNameserver


class MulticastNameserver(BaseNameserver):
    """
    Registers names ending in .local in multicast DNS
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._aiozc = zeroconf.asyncio.AsyncZeroconf(ip_version=zeroconf.IPVersion.All)
        self._registered: typing.Dict[str, zeroconf.ServiceInfo] = {}

    async def shutdown(self):
        await self._aiozc.async_unregister_all_services()
        await self._aiozc.async_close()

    async def add(self, rec: Record):
        if not rec.fqdn.endswith('.local.'):
            self._logger.warning(f'Ignoring registration as {rec.fqdn} does not '
                                 f'end with .local')
            return
        try:
            svc_fqdn = f'{rec.hostname}._http._tcp.{rec.domain}.'
            si = zeroconf.ServiceInfo(
                f'{rec.hostname}.local.',
                svc_fqdn,
                port=rec.port,  # Port is required by Apple, apparently
                addresses=[rec.ip_address],
                server=rec.fqdn)
            await self._aiozc.async_register_service(si)
            self._registered[rec.fqdn] = si
            self._logger.info(f'Added {rec.fqdn}')
        except zeroconf.BadTypeInNameException:
            self._logger.warning(f'Ignoring registration for {rec.fqdn} as it uses '
                                 f'a bad name')

    async def modify(self, rec: Record):
        if rec.fqdn not in self._registered:
            self._logger.warning(f'Ignoring update as {rec.fqdn} has not been '
                                 f'registered previously')
            return
        si = self._registered[rec.fqdn]
        si.port = rec.port
        si.addresses = [rec.ip_address]
        await self._aiozc.async_update_service(si)
        self._logger.info(f'Modified {rec.fqdn}')

    async def remove(self, rec):
        if rec.fqdn not in self._registered:
            self._logger.warning(f'Ignoring update as {rec.fqdn} has not been '
                                 f'registered previously')
            return
        await self._aiozc.async_unregister_service(self._registered[rec.fqdn])
        del self._registered[rec.fqdn]
        self._logger.info(f'Removed {rec.fqdn}')


class UnicastNameserver(BaseNameserver):
    """
    Registers names in a more traditional DNS nameserver
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._keyring = None
        if 'key' in kwargs and 'secret' in kwargs and kwargs['key'] is not None and kwargs['secret'] is not None:
            self._keyring = dns.tsigkeyring.from_text({kwargs['key']: kwargs['secret']})

    async def add(self, rec):
        try:
            add = dns.update.Update("nostromo.k8s", keyring=self._keyring)
            add.replace(rec.fqdn, 300, "A", rec.ip_addresses[0])
            response = dns.query.tcp(add, "127.0.0.1", timeout=10)
            if response.rcode() != dns.rcode.NOERROR:
                self._logger.warning(f'Failed to add {rec.fqdn}')
            else:
                self._logger.info(f'Added {rec.fqdn}.nostromo.k8s')
        except dns.exception.DNSException as de:
            self._logger.warning(f'Exception while adding {rec.fqdn}')

    async def modify(self, rec):
        try:
            update = dns.update.Update("nostromo.k8s", keyring=self._keyring)
            update.replace(rec.fqdn, 300, "A", rec.ip_addresses[0])
            response = dns.query.tcp(update, "127.0.0.1", timeout=10)
            if response.rcode() != dns.rcode.NOERROR:
                self._logger.warning(f'Failed to modify {rec.fqdn}')
            else:
                self._logger.info(f'Modified {rec.fqdn}.nostromo.k8s')
        except dns.exception.DNSException as de:
            self._logger.warning(f'Exception while modifying {rec.fqdn}')

    async def remove(self, rec):
        try:
            update = dns.update.Update("nostromo.k8s", keyring=self._keyring)
            update.delete(rec.fqdn, 300, "A", rec.ip_addresses[0])
            response = dns.query.tcp(update, "127.0.0.1", timeout=10)
            if response.rcode() != dns.rcode.NOERROR:
                self._logger.warning(f'Failed to remove {rec.fqdn}')
            else:
                self._logger.info(f'Removed {rec.fqdn}.nostromo.k8s')
        except dns.exception.DNSException as de:
            self._logger.warning(f'Exception while removing {rec.fqdn}')
