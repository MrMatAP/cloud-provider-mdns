#  MIT License
#
#  Copyright (c)  2025 Mathieu Imfeld
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import typing
import logging

import kubernetes_asyncio  # type: ignore[import-untyped]

from cloud_provider_mdns.base import (
    KubernetesGateway,
    HTTPRoute,
    Record,
    BaseNameserver,
)


class Registry:

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._gateways: typing.Dict[str, KubernetesGateway] = {}
        self._routes: typing.Dict[str, HTTPRoute] = {}
        self._ingresses: typing.Dict[
            str, kubernetes_asyncio.client.V1Ingress
        ] = {}

        self._records: typing.Set[Record] = set()
        self._subscribers: typing.Set[BaseNameserver] = set()

    async def add_record(self, record: Record):
        self._records.add(record)
        await self._notify_subscribers()
        self._logger.info(f"{record.owner_id} adds {record.hostname}")

    async def modify_record(self, record: Record):
        current = list(
            filter(
                lambda r: r.owner_id == record.owner_id
                and r.hostname == record.hostname,
                self._records,
            )
        )
        if len(current) == 0:
            await self.add_record(record)
            return
        self._records.remove(current[0])
        self._records.add(record)
        await self._notify_subscribers()
        self._logger.info(f"{record.owner_id} updates {record.hostname}")

    async def remove_record(self, record: Record):
        if record not in self._records:
            self._logger.warning(
                f"{record.owner_id} has already been removed from the registry"
            )
        else:
            self._records.remove(record)
        await self._notify_subscribers()
        self._logger.info(f"{record.owner_id} removes {record.hostname}")

    async def add_gateway(self, gateway: KubernetesGateway):
        gateway_id = f"{gateway.metadata.namespace}/{gateway.metadata.name}"
        if gateway_id in self._gateways:
            await self.modify_gateway(gateway)
            return
        self._gateways[gateway_id] = gateway
        self._logger.info(f"Added gateway {gateway_id}")
        for route in self._routes.values():
            resource_id = f"{route.metadata.namespace}/{route.metadata.name}"
            for parent_ref in route.spec.parentRefs:
                gateway_id = f"{parent_ref.namespace or route.metadata.namespace}/{parent_ref.name}"
                if not gateway_id in self._gateways:
                    self._logger.warning(
                        f"{resource_id} Specifies gateway {gateway_id} "
                        f"but it is not (yet) a known gateway"
                    )
                    continue
                gw = self._gateways[gateway_id]
                for hostname in route.spec.hostnames:
                    port = None
                    if parent_ref.port is not None:
                        port = parent_ref.port
                    elif parent_ref.sectionName is not None:
                        port = gw.port_by_section_name(parent_ref.sectionName)
                    if port is None:
                        port = 80
                    for ip_address in gw.addresses():
                        rec = Record(
                            owner_id=resource_id,
                            gateway_id=gateway_id,
                            hostname=hostname,
                            ip_address=ip_address,
                            port=port,
                        )
                        self._records.add(rec)
        await self._notify_subscribers()

    async def modify_gateway(self, gateway: KubernetesGateway):
        resource_id = f"{gateway.metadata.namespace}/{gateway.metadata.name}"
        if resource_id in self._gateways:
            await self.remove_gateway(gateway)
        await self.add_gateway(gateway)

    async def remove_gateway(self, gateway: KubernetesGateway):
        gateway_id = f"{gateway.metadata.namespace}/{gateway.metadata.name}"
        if not gateway_id in self._gateways:
            self._logger.warning(f"{gateway_id} is not a known gateway")
            return
        records = list(
            filter(lambda r: r.gateway_id == gateway_id, self._records)
        )
        for rec in records:
            self._records.remove(rec)
        del self._gateways[gateway_id]
        await self._notify_subscribers()

    async def add_route(self, route: HTTPRoute):
        resource_id = f"{route.metadata.namespace}/{route.metadata.name}"
        if resource_id in self._routes:
            await self.modify_route(route)
            return
        self._routes[resource_id] = route

        for parent_ref in route.spec.parentRefs:
            gateway_id = f"{parent_ref.namespace or route.metadata.namespace}/{parent_ref.name}"
            if not gateway_id in self._gateways:
                self._logger.warning(
                    f"{resource_id} specifies gateway {gateway_id} but it is "
                    f"not (yet) known"
                )
                continue
            gw = self._gateways[gateway_id]
            for hostname in route.spec.hostnames:
                port = None
                if parent_ref.port is not None:
                    port = parent_ref.port
                elif parent_ref.sectionName is not None:
                    port = gw.port_by_section_name(parent_ref.sectionName)
                if port is None:
                    port = 80
                for ip_address in gw.addresses():
                    rec = Record(
                        owner_id=resource_id,
                        gateway_id=gateway_id,
                        hostname=hostname,
                        ip_address=ip_address,
                        port=port,
                    )
                    self._records.add(rec)
        await self._notify_subscribers()

    async def modify_route(self, route: HTTPRoute):
        resource_id = f"{route.metadata.namespace}/{route.metadata.name}"
        if not resource_id in self._routes:
            self._logger.warning(f"{resource_id} is not a known HTTP route")
            return
        await self.remove_route(route)
        await self.add_route(route)

    async def remove_route(self, route: HTTPRoute):
        resource_id = f"{route.metadata.namespace}/{route.metadata.name}"
        if not resource_id in self._routes:
            self._logger.warning(f"{resource_id} is not a known HTTP route")
            return
        records = list(
            filter(lambda r: r.owner_id == resource_id, self._records)
        )
        for rec in records:
            self._records.remove(rec)
        del self._routes[resource_id]
        await self._notify_subscribers()

    async def add_ingress(self, ingress: kubernetes_asyncio.client.V1Ingress):
        resource_id = f"{ingress.metadata.namespace}/{ingress.metadata.name}"
        if resource_id in self._ingresses:
            await self.modify_ingress(ingress)
            return
        self._ingresses[resource_id] = ingress
        await self._notify_subscribers()

    async def modify_ingress(
        self, ingress: kubernetes_asyncio.client.V1Ingress
    ):
        resource_id = f"{ingress.metadata.namespace}/{ingress.metadata.name}"
        if resource_id in self._ingresses:
            await self.remove_ingress(ingress)
        await self.add_ingress(ingress)

    async def remove_ingress(
        self, ingress: kubernetes_asyncio.client.V1Ingress
    ):
        resource_id = f"{ingress.metadata.namespace}/{ingress.metadata.name}"
        if resource_id in self._ingresses:
            del self._ingresses[resource_id]
        await self._notify_subscribers()

    def records(self, domain: str | None = None) -> typing.Set[Record]:
        if domain is None:
            return self._records
        return set(filter(lambda r: r.fqdn.endswith(domain), self._records))

    def clear(self):
        self._records.clear()
        self._gateways.clear()
        self._routes.clear()
        self._ingresses.clear()

    def subscribe(self, ns: BaseNameserver):
        self._subscribers.add(ns)

    async def _notify_subscribers(self):
        records = self.records()
        for subscriber in self._subscribers:
            await subscriber.update(records)
