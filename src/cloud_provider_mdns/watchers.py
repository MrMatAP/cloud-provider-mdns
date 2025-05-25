import asyncio

import kubernetes_asyncio as kubernetes     # type: ignore[import-untyped]
from pydantic import ValidationError

from cloud_provider_mdns.base import \
    GatewayNotReadyException, UnidentifiableResourceException, HTTPRoute, Gateway, \
    BaseWatcher, Record
from cloud_provider_mdns.registry import Registry


class GatewayWatcher(BaseWatcher):

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.CustomObjectsApi()

    async def run(self):
        if not await self._has_api(required_api_name='gateway.networking.k8s.io'):
            self._logger.warning('Not watching for Gateways because the cluster you are connected to does not know the Gateway API')
            return
        self._logger.info('Watching for Gateways')
        try:
            while True:
                if self._should_stop:
                    self._watch.stop()
                    return
                try:
                    async for event in self._watch.stream(self._api.list_cluster_custom_object,
                                                          'gateway.networking.k8s.io',
                                                          'v1',
                                                          'gateways'):
                        gateway = Gateway.model_validate(event['object'])
                        match event['type']:
                            case 'ADDED':
                                await self._registry.add_gateway(gateway)
                            case 'MODIFIED':
                                await self._registry.modify_gateway(gateway)
                            case 'DELETED':
                                await self._registry.remove_gateway(gateway)
                except ValidationError as ve:
                    self._logger.warning(ve)
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


class HTTPRouteWatcher(BaseWatcher):

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.CustomObjectsApi()

    async def run(self):
        if not await self._has_api(required_api_name='gateway.networking.k8s.io'):
            self._logger.warning('Not watching for HTTPRoutes because the cluster you are connected to does not know the Gateway API.')
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
                        route = HTTPRoute.model_validate(event['object'])
                        match event['type']:
                            case 'ADDED':
                                await self._registry.add_route(route)
                            case 'MODIFIED':
                                await self._registry.modify_route(route)
                            case 'DELETED':
                                await self._registry.remove_route(route)
                except ValidationError as ve:
                    self._logger.warning(ve)
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

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.NetworkingV1Api()

    async def run(self):
        self._logger.info('Watching for Ingresses')
        try:
            while True:
                async for event in self._watch.stream(self._api.list_ingress_for_all_namespaces):
                    ingress = event['object']
                    if ingress.status.load_balancer.ingress is None or ingress.status.load_balancer.ingress[0].ip is None:
                        self._logger.warning(f'Skipping ingress {ingress.metadata.name}/{ingress.metadata.namespace} because it has no load_balancer IP injected yet')
                        continue
                    if len(ingress.status.load_balancer.ingress) > 1:
                        self._logger.warning(f'Skipping Ingress {ingress.metadata.name}/{ingress.metadata.namespace} has multiple load_balancer ingress IPs injected. '
                                             f'Only the first one will be used.')
                    record = Record(owner_id=f'{ingress.metadata.namespace}/{ingress.metadata.name}',
                                    hostname=ingress.spec.rules[0].host,
                                    ip_address=ingress.status.load_balancer.ingress[0].ip,
                                    port=80)
                    match event['type']:
                        case 'ADDED':
                            self._logger.info(f'Discovered new ingress {record.owner_id} for hostname {record.hostname} pointing to {record.ip_address}:{record.port}')
                            await self._registry.add_record(record)
                        case 'MODIFIED':
                            self._logger.info(f'Modified Ingress: {ingress.metadata.name}')
                            await self._registry.modify_record(record)
                        case 'DELETED':
                            self._logger.info(f'Deleted Ingress: {ingress.metadata.name}')
                            await self._registry.remove_record(record)
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
