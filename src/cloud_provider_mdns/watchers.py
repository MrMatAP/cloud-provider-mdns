import typing
import asyncio

import kubernetes_asyncio as kubernetes

from cloud_provider_mdns.base import BaseTask, NSRecord, \
    GatewayNotReadyException, ResourceId, UnidentifiableResourceException, HTTPRoute, Gateway, \
    NSAddressPort
from cloud_provider_mdns.registries import RecordRegistry


class BaseWatcher(BaseTask):

    def __init__(self, record_registry: RecordRegistry = None):
        super().__init__()
        self._watch = kubernetes.watch.Watch()
        self._record_registry = record_registry

    async def run(self):
        raise NotImplementedError

    async def add(self, event):
        raise NotImplementedError

    async def modify(self, event):
        raise NotImplementedError

    async def remove(self, event):
        raise NotImplementedError

    @staticmethod
    async def _has_api(required_api_name: str) -> bool:
        """
        Return true when the cluster is aware of the provided API
        """
        apis_api = kubernetes.client.ApisApi()
        resources = await apis_api.get_api_versions()
        return list(filter(lambda r: r.name == required_api_name, resources.groups)) != []


class HTTPRouteWatcher(BaseWatcher):

    def __init__(self, record_registry: RecordRegistry):
        super().__init__(record_registry)
        self._api = kubernetes.client.CustomObjectsApi()

    async def add(self, event):
        http_route = HTTPRoute.model_validate(event['object'])
        if not http_route.accepted():
            self._logger.warning(f'[{http_route}] has not yet been accepted')
            return
        for parent in http_route.status.parents:
            gtw = await self._api.get_namespaced_custom_object(group='gateway.networking.k8s.io',
                                                               version='v1',
                                                               namespace=parent.parentRef.namespace,
                                                               plural='gateways',
                                                               name=parent.parentRef.name)
            gateway = Gateway.model_validate(gtw)
            port = gateway.listener_by_section_name(section_name=parent.parentRef.sectionName).port or 80
            for hostname in http_route.spec.hostnames:
                record = NSRecord(namespace=http_route.metadata.namespace,
                                  name=http_route.metadata.name,
                                  hostname=hostname,
                                  address_ports=[
                                      NSAddressPort(ip_addresses=gateway.addresses(), port=port)])
                await self._record_registry.add_record(record)
                self._logger.info(f'[{http_route}] Discovered HTTPRoute')

    async def modify(self, event):
        http_route = HTTPRoute.model_validate(event['object'])
        auth_known_recs = self._record_registry.by_owner(http_route.metadata.namespace,
                                                         http_route.metadata.name)
        for rec in auth_known_recs:
            for parent in http_route.status.parents:
                gtw = await self._api.get_namespaced_custom_object(group='gateway.networking.k8s.io',
                                                                   version='v1',
                                                                   namespace=parent.parentRef.namespace,
                                                                   plural='gateways',
                                                                   name=parent.parentRef.name)
                gateway = Gateway.model_validate(gtw)
                port = gateway.listener_by_section_name(
                    section_name=parent.parentRef.sectionName).port or 80
                rec.address_ports = [NSAddressPort(ip_addresses=gateway.addresses(), port=port)]
                await self._record_registry.add_record(rec)
                self._logger.info(f'[{http_route}] Modified HTTPRoute')

    async def remove(self, event):
        http_route = HTTPRoute.model_validate(event['object'])
        auth_known_recs = self._record_registry.by_owner(http_route.metadata.namespace,
                                                         http_route.metadata.name)
        for rec in auth_known_recs:
            await self._record_registry.remove_record(rec)
            self._logger.info(f'[{http_route}] Removed HTTPRoute')

    async def run(self):
        if not await self._has_api(required_api_name='gateway.networking.k8s.io'):
            self._logger.warning(f'Kubernetes cluster does not know the Gateway API. '
                                 f'Not watching for HTTPRoutes.')
            return
        self._logger.info('Watching for HTTPRoutes')
        try:
            while True:
                if self._should_stop:
                    self._watch.stop()
                    return
                try:
                    async for event in self._watch.stream(self._api.list_cluster_custom_object,
                                                          'gateway.networking.k8s.io',
                                                          'v1',
                                                          'httproutes'):
                        match event['type']:
                            case 'ADDED':
                                await self.add(event)
                            case 'MODIFIED':
                                await self.modify(event)
                            case 'DELETED':
                                await self.remove(event)
                except UnidentifiableResourceException as ur:
                    self._logger.warning(ur)
                except GatewayNotReadyException as gnre:
                    self._logger.warning(gnre)
                except kubernetes.client.exceptions.ApiException:
                    self._logger.info('Kubernetes API error, restarting')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            self._should_stop = True
            await self._watch.close()
            raise

class IngressWatcher(BaseWatcher):

    def __init__(self, record_registry: RecordRegistry):
        super().__init__()
        self._api = kubernetes.client.NetworkingV1Api()
        self._record_registry = record_registry

    async def run(self):
        if not await self._has_api(required_api_name='networking.k8s.io'):
            self._logger.warning(f'Kubernetes cluster does not know the networking.k8s.io API. '
                                 f'Not watching for Ingresses.')
            return
        self._logger.info('Watching for Ingresses')
        try:
            while True:
                if self._should_stop:
                    self._watch.stop()
                    return
                try:
                    async for event in self._watch.stream(
                            self._api.list_ingress_for_all_namespaces):
                        resource_id = ResourceId.from_resource(event['object'])
                        if event['type'] == 'DELETED':
                            self._logger.info(f'Removing Ingress {resource_id}')
                        ing = event['object']
                        if (ing.status.load_balancer is None or
                                ing.status.load_balancer.ingress is None or
                                len(ing.status.load_balancer.ingress) == 0):
                            self._logger.warning(
                                f'Skipping Ingress {ing.metadata.namespace}/{ing.metadata.name} '
                                f'as it does not have a hostname just yet')
                            continue
                        elif len(ing.status.load_balancer.ingress) > 1:
                            self._logger.warning(
                                f'Skipping Ingress {ing.metadata.namespace}/{ing.metadata.name} '
                                f'as it has multiple hostnames, which is not supported yet.')
                            continue
                        auth_id = f'{ing.metadata.namespace}/{ing.metadata.name}'
                        controller_ip = ing.status.load_balancer.ingress[0].ip
                        if controller_ip is None and ing.status.load_balancer.ingress[
                            0].hostname == 'localhost':
                            controller_ip = '127.0.0.1'

                        #
                        # Find records to be removed

                        auth_known_recs = self._record_registry.by_owner(ing.metadata.namespace,
                                                                         ing.metadata.name)
                        if event['type'] == 'DELETED':
                            for rec in auth_known_recs:
                                await self._record_registry.remove_record(rec)
                            continue
                        ing_fqdns = [r.host for r in ing.spec.rules]
                        for rec in auth_known_recs:
                            if rec.fqdn not in ing_fqdns:
                                await self._record_registry.remove_record(rec)

                        #
                        # Find records to add or change

                        for hostname in ing_fqdns:
                            rec = self._record_registry.by_fqdn(hostname)
                            if rec:
                                rec.port = 80  # TODO: This is an assumption
                                rec.ip_addresses = [controller_ip]
                                await self._record_registry.modify_record(rec)
                            else:
                                rec = NSRecord(namespace=ing.metadata.namespace,
                                               name=ing.metadata.name,
                                               fqdn=hostname,
                                               svc='_http._tcp',
                                               port=80,  # TODO: This is an assumption
                                               ip_addresses=[controller_ip])
                                await self._record_registry.add_record(rec)
                        match event['type']:
                            case 'ADDED':
                                self._logger.info(f'Discovered Ingress {auth_id}')
                            case 'MODIFIED':
                                self._logger.info(f'Ingress {auth_id} was modified')
                            case 'DELETED':
                                self._logger.info(f'Ingress {auth_id} was removed')
                except kubernetes.client.exceptions.ApiException:
                    self._logger.info('Kubernetes API error, restarting')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            self._should_stop = True
            await self._watch.close()
            raise
