import typing
import ipaddress

import zeroconf
import zeroconf.asyncio
import dns.message
import dns.update
import dns.tsigkeyring
import dns.query
import dns.rcode
import dns.exception
import zeroconf.asyncio

from cloud_provider_mdns.base import Record, BaseNameserver
from cloud_provider_mdns.registry import Registry


class MulticastNameserver(BaseNameserver):
    """
    Registers names ending in .local in multicast DNS
    """

    def __init__(self, registry: Registry, *args, **kwargs) -> None:
        super().__init__(registry, *args, **kwargs)
        self._aiozc = zeroconf.asyncio.AsyncZeroconf(ip_version=zeroconf.IPVersion.All)
        self._registered: typing.Dict[Record, zeroconf.asyncio.AsyncServiceInfo] = {}

    async def shutdown(self):
        await self._aiozc.async_unregister_all_services()
        await self._aiozc.async_close()

    async def update(self, records: typing.Set[Record]):

        # Filter out records that do not end in .local.
        local_records = set(filter(lambda r: r.fqdn.endswith('.local.'), records))

        # Remove records
        for rec in set(self._registered.keys()).difference(local_records):
            await self._aiozc.async_unregister_service(self._registered[rec])
            del self._registered[rec]
            self._logger.info(f'{rec.owner_id} - Removed {rec.fqdn}')

        # Add records
        for rec in local_records.difference(self._registered):
            try:
                svc_fqdn = f'{rec.unqualified}.covenant._http._tcp.local.'
                si = zeroconf.asyncio.AsyncServiceInfo(
                    '_http._tcp.local.',
                    svc_fqdn,
                    port=rec.port,  # Port is required by Apple, apparently
                    addresses=[rec.ip_address],
                    server=rec.fqdn)
                await self._aiozc.async_register_service(si, allow_name_change=True)
                self._registered[rec] = si
                self._logger.info(f'Added {rec.fqdn} pointing to {rec.ip_address}:{rec.port} for {rec.owner_id}')
            except zeroconf.BadTypeInNameException:
                self._logger.warning(f'Ignoring {rec.owner_id} because {rec.fqdn} is invalid')
            except zeroconf.ServiceNameAlreadyRegistered:
                self._logger.warning(f'Ignoring {rec.owner_id} because {rec.fqdn} is already registered')

        # Modify records
        for rec in set(self._registered.keys()).intersection(local_records):
            si = self._registered[rec]
            if si.port != rec.port:
                si.port = rec.port
                self._logger.info(f'Modified port from {si.port} to {rec.port} for {rec.owner_id}')
            old_ip = ipaddress.ip_interface(si.addresses[0])
            new_ip = ipaddress.ip_interface(rec.ip_address)
            if old_ip.ip != new_ip.ip:
                si.addresses = [rec.ip_address]
                self._logger.info(f'Modified IP address from {old_ip} to {new_ip} for {rec.owner_id}')
            await self._aiozc.async_update_service(si)


class UnicastNameserver(BaseNameserver):
    """
    Registers names in a more traditional DNS nameserver
    """

    def __init__(self, registry: Registry, *args, **kwargs):
        super().__init__(registry)
        self._registered: typing.Set[Record] = set()
        self._keyring = None
        if 'key' in kwargs and 'secret' in kwargs and kwargs['key'] is not None and kwargs['secret'] is not None:
            self._keyring = dns.tsigkeyring.from_text({kwargs['key']: kwargs['secret']})

    async def update(self, records: typing.Set[Record]):
        # Remove records
        for rec in records.difference(self._registered):
            try:
                update = dns.update.Update("nostromo.k8s", keyring=self._keyring)
                update.delete(rec.fqdn, 300, "A", rec.ip_address)
                response = dns.query.tcp(update, "127.0.0.1", timeout=10)
                if response.rcode() != dns.rcode.NOERROR:
                    self._logger.warning(f'Failed to remove {rec.fqdn}')
                else:
                    self._logger.info(f'Removed {rec.fqdn}.nostromo.k8s')
            except dns.exception.DNSException as de:
                self._logger.warning(f'Exception while removing {rec.fqdn}')

        # Add records
        for rec in records.difference(self._registered):
            try:
                add = dns.update.Update("nostromo.k8s", keyring=self._keyring)
                add.replace(rec.fqdn, 300, "A", rec.ip_address)
                response = dns.query.tcp(add, "127.0.0.1", timeout=10)
                if response.rcode() != dns.rcode.NOERROR:
                    self._logger.warning(f'Failed to add {rec.fqdn}')
                else:
                    self._logger.info(f'Added {rec.fqdn}.nostromo.k8s')
            except dns.exception.DNSException as de:
                self._logger.warning(f'Exception while adding {rec.fqdn}')

        # Modify records
        for rec in set(self._registered).intersection(records):
            try:
                update = dns.update.Update("nostromo.k8s", keyring=self._keyring)
                update.replace(rec.fqdn, 300, "A", rec.ip_address)
                response = dns.query.tcp(update, "127.0.0.1", timeout=10)
                if response.rcode() != dns.rcode.NOERROR:
                    self._logger.warning(f'Failed to modify {rec.fqdn}')
                else:
                    self._logger.info(f'Modified {rec.fqdn}.nostromo.k8s')
            except dns.exception.DNSException as de:
                self._logger.warning(f'Exception while modifying {rec.fqdn}')
