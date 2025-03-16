import typing
import asyncio

import kubernetes_asyncio as kubernetes

from cloud_provider_mdns.base import BaseTask, NSRecord, Gateway, GatewayListener, \
    GatewayNotReadyException, ResourceId, UnidentifiableResourceException
from cloud_provider_mdns.registries import RecordRegistry


class BaseWatcherTask(BaseTask):

    def __init__(self):
        super().__init__()
        self._watch = kubernetes.watch.Watch()

    @staticmethod
    async def _has_api(required_api_name: str) -> bool:
        """
        Return true when the cluster is aware of the provided API
        """
        apis_api = kubernetes.client.ApisApi()
        resources = await apis_api.get_api_versions()
        return list(filter(lambda r: r.name == required_api_name, resources.groups)) != []

    async def run(self):
        raise NotImplementedError


class HTTPRouteWatcher(BaseWatcherTask):

    def __init__(self, record_registry: RecordRegistry):
        super().__init__()
        self._api = kubernetes.client.CustomObjectsApi()
        self._record_registry = record_registry

    async def _resolve_gtw(self, namespace: str, name: str) -> Gateway:
        """
        Resolve the IP address of the Gateway

        """
        if namespace is None or name is None:
            raise UnidentifiableResourceException(code=400,
                                                  msg='Missing namespace or name to resolve Gateway')
        gtw = await self._api.get_namespaced_custom_object(group='gateway.networking.k8s.io',
                                                           version='v1',
                                                           namespace=namespace,
                                                           plural='gateways',
                                                           name=name)
        gtw_addresses = gtw.get('status', {}).get('addresses', [])
        gtw_listeners = gtw.get('spec', {}).get('listeners', [])
        listeners = [GatewayListener(port=l.get('port'),
                                     protocol=l.get('protocol'),
                                     ip_addresses=[a.get('value') for a in gtw_addresses])
                     for l in gtw_listeners]
        if len(listeners) == 0:
            raise GatewayNotReadyException(code=400,
                                           msg='Gateway is not ready yet')
        return Gateway(namespace=namespace,
                       name=name,
                       listeners=listeners)

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
                        resource_id = ResourceId.from_resource(event['object'])
                        if event['type'] == 'DELETED':
                            self._logger.info(f'Removing HTTPRoute {resource_id}')
                            # TODO
                            continue
                        hostnames = event['object'].get('spec', {}).get('hostnames', [])
                        if len(hostnames) == 0:
                            self._logger.warning(f'Skipping HTTPRoute {resource_id} without hostnames')
                            continue
                        parents = event['object'].get('status', {}).get('parents', [])
                        if len(parents) == 0:
                            self._logger.warning(f'Skipping HTTPRoute {resource_id} '
                                                 f'without parents')
                            continue
                        if len(parents) > 1:
                            self._logger.warning(f'Skipping HTTPRoute {resource_id} '
                                                 f'with multiple parents')
                            continue
                        accepted = list(filter(lambda c: c.get('type', '') == 'Accepted',
                                               parents[0].get('conditions', [])))
                        if len(accepted) == 0 or accepted[0].get('status', '') != 'True':
                            self._logger.warning(f'Skipping HTTPRoute {resource_id} '
                                                 f'without accepted condition')
                            continue
                        parent_namespace = parents[0].get('parentRef', {}).get('namespace', None)
                        parent_name = parents[0].get('parentRef', {}).get('name', None)
                        gtw = await self._resolve_gtw(parent_namespace, parent_name)

                        #
                        # Find records to be removed

                        auth_known_recs = self._record_registry.by_owner(resource_id.namespace,
                                                                         resource_id.name)
                        if event['type'] == 'DELETED':
                            for rec in auth_known_recs:
                                await self._record_registry.remove_record(rec)
                            continue
                        for rec in auth_known_recs:
                            if rec.fqdn not in hostnames:
                                await self._record_registry.remove_record(rec)

                        #
                        # Find records to add or change

                        for hostname in hostnames:
                            rec = self._record_registry.by_fqdn(hostname)
                            if rec:
                                rec.port = gtw.listeners[0].port
                                rec.ip_addresses = gtw.listeners[0].ip_addresses
                                await self._record_registry.modify_record(rec)
                            else:
                                rec = NSRecord(owner_namespace=resource_id.namespace,
                                               owner_name=resource_id.name,
                                               fqdn=hostname,
                                               svc='_http._tcp',
                                               port=gtw.listeners[0].port,
                                               ip_addresses=gtw.listeners[0].ip_addresses)
                                await self._record_registry.add_record(rec)
                        match event['type']:
                            case 'ADDED':
                                self._logger.info(f'Discovered HTTPRoute {resource_id}')
                            case 'MODIFIED':
                                self._logger.info(f'HTTPRoute {resource_id} was modified')
                            case 'DELETED':
                                self._logger.info(f'HTTPRoute {resource_id} was removed')
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


class IngressWatcher(BaseWatcherTask):

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
                    async for event in self._watch.stream(self._api.list_ingress_for_all_namespaces):
                        resource_id = ResourceId.from_resource(event['object'])
                        if event['type'] == 'DELETED':
                            self._logger.info(f'Removing Ingress {resource_id}')
                        ing = event['object']
                        if (ing.status.load_balancer is None or
                                ing.status.load_balancer.ingress is None or
                                len(ing.status.load_balancer.ingress) == 0):
                            self._logger.warning(f'Skipping Ingress {ing.metadata.namespace}/{ing.metadata.name} '
                                                 f'as it does not have a hostname just yet')
                            continue
                        elif len(ing.status.load_balancer.ingress) > 1:
                            self._logger.warning(f'Skipping Ingress {ing.metadata.namespace}/{ing.metadata.name} '
                                                 f'as it has multiple hostnames, which is not supported yet.')
                            continue
                        auth_id = f'{ing.metadata.namespace}/{ing.metadata.name}'
                        controller_ip = ing.status.load_balancer.ingress[0].ip
                        if controller_ip is None and ing.status.load_balancer.ingress[0].hostname == 'localhost':
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
                                rec.port = 80   # TODO: This is an assumption
                                rec.ip_addresses = [controller_ip]
                                await self._record_registry.modify_record(rec)
                            else:
                                rec = NSRecord(owner_namespace=ing.metadata.namespace,
                                               owner_name=ing.metadata.name,
                                               fqdn=hostname,
                                               svc='_http._tcp',
                                               port=80,     # TODO: This is an assumption
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
