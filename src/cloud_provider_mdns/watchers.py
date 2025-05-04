import asyncio

import kubernetes_asyncio as kubernetes
from pydantic import ValidationError

from cloud_provider_mdns.base import \
    GatewayNotReadyException, UnidentifiableResourceException, HTTPRoute, Gateway, \
    BaseWatcher
from cloud_provider_mdns.registry import Registry


class GatewayWatcher(BaseWatcher):

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.CustomObjectsApi()

    async def run(self):
        if not await self._has_api(required_api_name='gateway.networking.k8s.io'):
            self._logger.warning(f'Kubernetes cluster does not know the Gateway API. '
                                 f'Not watching for Gateways.')
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
