import asyncio

import kubernetes_asyncio as kubernetes     # type: ignore[import-untyped]

from cloud_provider_mdns.base import (
    GatewayNotReadyException, UnidentifiableResourceException,
    BaseWatcher, Record,
    HTTPRoute, Gateway,
    VirtualService, NativeIstioGateway )
from cloud_provider_mdns.registry import Registry


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
                    await self.register_record(event['type'], record)
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

class VirtualServiceWatcher(BaseWatcher):

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.CustomObjectsApi()
        self._core_api = kubernetes.client.CoreV1Api()

    async def run(self):
        if not await self._has_api(required_api_name='networking.istio.io'):
            self._logger.warning('Not watching for VirtualServices because the cluster you are connected to does not know them')
            return
        self._logger.info('Watching for VirtualServices')
        try:
            while True:
                async for event in self._watch.stream(self._api.list_cluster_custom_object,
                                                      'networking.istio.io',
                                                      'v1',
                                                      'virtualservices'):
                    virtualservice = VirtualService.model_validate(event['object'])
                    # Filter out the mesh gateway, if present
                    gateways = list(filter(lambda g: g != "mesh", virtualservice.spec.gateways))
                    if len(gateways) > 1:
                        self._logger.warning(f'VirtualService {virtualservice.metadata.name}/{virtualservice.metadata.namespace} has multiple gateways configured. Only the first one will be used.')
                    if len(gateways) == 0:
                        self._logger.warning(f'Skipping VirtualService {virtualservice.metadata.name}/{virtualservice.metadata.namespace} because it has no gateways configured')
                        continue
                    # The gateway namespace may be different from the virtualservice namespace
                    if '/' in gateways[0]:
                        gw_ns, gw_name = gateways[0].split('/')
                    else:
                        gw_ns = virtualservice.metadata.namespace
                        gw_name = gateways[0]
                    # Look up the gateway in the same namespace as the virtualservice.
                    gw_raw = await self._api.get_namespaced_custom_object(group='networking.istio.io',
                                                                      version='v1',
                                                                      namespace=gw_ns,
                                                                      plural='gateways',
                                                                      name=gw_name)
                    gw = NativeIstioGateway.model_validate(gw_raw)
                    # Find all Services of type LoadBalancer and filter them on the selector of our gateway
                    lb_svcs = await self._core_api.list_service_for_all_namespaces(field_selector='spec.type=LoadBalancer')
                    lb_svc = list(filter(lambda s: s.spec.selector == gw.spec.selector, lb_svcs.items))
                    if len(lb_svc) == 0:
                        self._logger.warning(f'Skipping VirtualService {virtualservice.metadata.name}/{virtualservice.metadata.namespace} because no exposed service can be resolved for it')
                        continue
                    record = Record(owner_id=f'{virtualservice.metadata.namespace}/{virtualservice.metadata.name}',
                                    hostname=virtualservice.spec.hosts[0],
                                    ip_address=lb_svc[0].status.load_balancer.ingress[0].ip,
                                    port=80)
                    await self.register_record(event['type'], record)
        except UnidentifiableResourceException as ur:
            self._logger.warning(ur)
        except GatewayNotReadyException as gnre:
            self._logger.warning(gnre)
        except kubernetes.client.exceptions.ApiException as ae:
            self._logger.info('Kubernetes API error, restarting')
        except asyncio.CancelledError:
            self._logger.info('Stopping')
            self._should_stop = True
            await self._watch.close()
            raise
