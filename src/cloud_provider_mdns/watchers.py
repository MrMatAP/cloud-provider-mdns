import typing
import asyncio

import kubernetes_asyncio as kubernetes
from k8s_gateway_api import IoK8sNetworkingGatewayV1HTTPRoute
from base import BaseTask, NSUpdate, NSUpdateType

class HTTPRouteWatcher(BaseTask):

    def __init__(self, api: kubernetes.client.CustomObjectsApi, q: asyncio.Queue):
        super().__init__()
        self._api = api
        self._q = q
        self._known: typing.List[str] = []

    async def run(self):
        try:
            self._logger.info('Starting')
            while True:
                try:
                    w = kubernetes.watch.Watch()
                    async for event in w.stream(self._api.list_cluster_custom_object,
                                                'gateway.networking.k8s.io',
                                                'v1',
                                                'httproutes'):
                        route = IoK8sNetworkingGatewayV1HTTPRoute.model_validate(event['object'])
                        if len(route.spec.hostnames) > 1:
                            self._logger.warning(f'Multiple hostnames in HTTPRoute {route.metadata.namespace}/{route.metadata.name} are not yet supported.')
                        hostname = route.spec.hostnames[0]
                        # Try to find the gateways this httproute is attached to
                        addrs: typing.List[str] = []
                        for parent in route.status.parents:
                            gtw_raw = await self._api.get_namespaced_custom_object('gateway.networking.k8s.io',
                                                                             'v1',
                                                                             parent.parent_ref.namespace,
                                                                             'gateways',
                                                                             parent.parent_ref.name)
                            addresses = gtw_raw.get('status', {}).get('addresses', {})
                            for addr in addresses:
                                addrs.append(addr.get('value'))
                        name_reg = NSUpdate(
                            update=NSUpdateType.ADD,
                            name=hostname.replace('.local', ''),
                            svc='_http._tcp.local.',  # TODO: We should not make this assumption
                            port=80,  # TODO: We should not make this assumption
                            ip_addresses=addrs)
                        match event['type']:
                            case 'ADDED':
                                name_reg.update = NSUpdateType.ADD if name_reg.svc_fqdn not in self._known else NSUpdateType.MODIFY
                                self._logger.info(
                                    f'Adding new HTTPRoute {route.metadata.namespace}/{route.metadata.name}')
                            case 'MODIFIED':
                                name_reg.update = NSUpdateType.MODIFY
                                self._logger.info(
                                    f'Modifying HTTPRoute {route.metadata.namespace}/{route.metadata.name}')
                            case 'DELETED':
                                name_reg.update = NSUpdateType.REMOVE
                                self._logger.info(
                                    f'Removing HTTPRoute {route.metadata.namespace}/{route.metadata.name}')
                        await self._q.put(name_reg)
                        self._known.append(name_reg.svc_fqdn)
                except kubernetes.client.exceptions.ApiException as ae:
                    self._logger.info('Kubernetes API error, restarting')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            raise
