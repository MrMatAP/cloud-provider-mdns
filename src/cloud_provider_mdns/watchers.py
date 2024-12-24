import asyncio

import kubernetes_asyncio as kubernetes # type: ignore

from k8s_gateway_api import IoK8sNetworkingGatewayV1HTTPRoute
from cloud_provider_mdns.base import BaseTask, NSRecord
from cloud_provider_mdns.registries import RecordRegistry, GatewayRegistry


class HTTPRouteWatcher(BaseTask):

    def __init__(self,
                 api: kubernetes.client.CustomObjectsApi,
                 record_registry: RecordRegistry,
                 gtw_registry: GatewayRegistry):
        super().__init__()
        self._api = api
        self._gtw_registry = gtw_registry
        self._record_registry = record_registry
        self._should_stop = False
        self._watch = kubernetes.watch.Watch()

    async def run(self):
        self._logger.info('Starting')
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
                        route = IoK8sNetworkingGatewayV1HTTPRoute.model_validate(event['object'])
                        auth_id = f'{route.metadata.namespace}/{route.metadata.name}'
                        if len(route.spec.hostnames) == 0:
                            self._logger.warning(f'Skipping HTTPRoute {auth_id} without hostnames')
                            continue
                        if len(route.status.parents) == 0:
                            self._logger.warning(f'Skipping HTTPRoute {auth_id} without gateway '
                                                 f'parent')
                            continue
                        elif len(route.status.parents) > 1:
                            self._logger.warning(f'Multiple gateways in HTTPRoute {auth_id}. '
                                                 f'Will only register for the first gateway')
                        gtw = await self._gtw_registry.get_gtw(
                            route.status.parents[0].parent_ref.namespace,
                            route.status.parents[0].parent_ref.name)

                        #
                        # Find records to be removed

                        auth_known_recs = self._record_registry.by_owner(route.metadata.namespace,
                                                                         route.metadata.name)
                        for rec in auth_known_recs:
                            if rec.fqdn not in route.spec.hostnames:
                                await self._record_registry.remove_record(rec)

                        #
                        # Find records to add or change

                        for hostname in route.spec.hostnames:
                            rec = self._record_registry.by_fqdn(hostname)
                            if rec:
                                rec.port = gtw.listeners[0].port
                                rec.ip_addresses = gtw.listeners[0].ip_addresses
                                await self._record_registry.modify_record(rec)
                            else:
                                rec = NSRecord(owner_namespace=route.metadata.namespace,
                                               owner_name=route.metadata.name,
                                               fqdn=hostname,
                                               svc='_http._tcp',
                                               port=gtw.listeners[0].port,
                                               ip_addresses=gtw.listeners[0].ip_addresses)
                                await self._record_registry.add_record(rec)
                        match event['type']:
                            case 'ADDED':
                                self._logger.info(f'Discovered HTTPRoute {auth_id}')
                            case 'MODIFIED':
                                self._logger.info(f'HTTPRoute {auth_id} was modified')
                            case 'DELETED':
                                self._logger.info(f'HTTPRoute {auth_id} was removed')
                except kubernetes.client.exceptions.ApiException:
                    self._logger.info('Kubernetes API error, restarting')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            self._should_stop = True
            await self._watch.close()
            raise
