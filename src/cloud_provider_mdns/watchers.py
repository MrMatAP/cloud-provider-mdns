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

import asyncio

import aiohttp.client_exceptions
import kubernetes_asyncio as kubernetes  # type: ignore[import-untyped]
import pydantic

from cloud_provider_mdns.base import (
    GatewayNotReadyException,
    UnidentifiableResourceException,
    BaseWatcher,
    Record,
    HTTPRoute,
    KubernetesGateway,
    VirtualService,
    NativeIstioGateway,
)
from cloud_provider_mdns.registry import Registry


class IngressWatcher(BaseWatcher):
    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.NetworkingV1Api()

    async def run(self):
        self._logger.info("Watching for Ingresses")
        try:
            while True:
                async for event in self._watch.stream(
                    self._api.list_ingress_for_all_namespaces
                ):
                    ingress = event["object"]
                    if (
                        ingress.status.load_balancer.ingress is None
                        or ingress.status.load_balancer.ingress[0].ip is None
                    ):
                        self._logger.warning(
                            f"Skipping ingress {ingress.metadata.name}/{ingress.metadata.namespace} because it has no load_balancer IP injected yet"
                        )
                        continue
                    if len(ingress.status.load_balancer.ingress) > 1:
                        self._logger.warning(
                            f"Skipping Ingress {ingress.metadata.name}/{ingress.metadata.namespace} has multiple load_balancer ingress IPs injected. "
                            f"Only the first one will be used."
                        )
                    record = Record(
                        owner_id=f"{ingress.metadata.namespace}/{ingress.metadata.name}",
                        hostname=ingress.spec.rules[0].host,
                        ip_address=ingress.status.load_balancer.ingress[0].ip,
                        port=80,
                    )
                    await self.register_record(event["type"], record)
        except UnidentifiableResourceException as ur:
            self._logger.warning(ur)
        except GatewayNotReadyException as gnre:
            self._logger.warning(gnre)
        except kubernetes.client.exceptions.ApiException:
            self._logger.info("Kubernetes API error, restarting")
        except aiohttp.client_exceptions.ClientError as ce:
            self._logger.info(f"Client error while connecting to Kubernetes API: {ce}")
        except asyncio.CancelledError:
            self._logger.info("Stopping")
            self._should_stop = True
            await self._watch.close()
            raise


class VirtualServiceWatcher(BaseWatcher):
    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.CustomObjectsApi()
        self._core_api = kubernetes.client.CoreV1Api()

    async def run(self):
        if not await self._has_api(required_api_name="networking.istio.io"):
            self._logger.warning(
                "Not watching for VirtualServices because the cluster you are connected to does not know them"
            )
            return
        self._logger.info("Watching for VirtualServices")
        try:
            while True:
                async for event in self._watch.stream(
                    self._api.list_cluster_custom_object,
                    "networking.istio.io",
                    "v1",
                    "virtualservices",
                ):
                    virtualservice = VirtualService.model_validate(event["object"])
                    # Filter out the mesh gateway, if present
                    gateways = list(
                        filter(lambda g: g != "mesh", virtualservice.spec.gateways)
                    )
                    if len(gateways) > 1:
                        self._logger.warning(
                            f"VirtualService {virtualservice.metadata.name}/{virtualservice.metadata.namespace} has multiple gateways configured. Only the first one will be used."
                        )
                    if len(gateways) == 0:
                        self._logger.warning(
                            f"Skipping VirtualService {virtualservice.metadata.name}/{virtualservice.metadata.namespace} because it has no gateways configured"
                        )
                        continue
                    # The gateway namespace may be different from the virtualservice namespace
                    if "/" in gateways[0]:
                        gw_ns, gw_name = gateways[0].split("/")
                    else:
                        gw_ns = virtualservice.metadata.namespace
                        gw_name = gateways[0]
                    # Look up the gateway
                    gw_raw = await self._api.get_namespaced_custom_object(
                        group="networking.istio.io",
                        version="v1",
                        namespace=gw_ns,
                        plural="gateways",
                        name=gw_name,
                    )
                    gw = NativeIstioGateway.model_validate(gw_raw)
                    # Find all Services of type LoadBalancer and filter them on the selector of our gateway
                    lb_svcs = await self._core_api.list_service_for_all_namespaces(
                        field_selector="spec.type=LoadBalancer"
                    )
                    lb_svc = list(
                        filter(
                            lambda s: s.spec.selector == gw.spec.selector,
                            lb_svcs.items,
                        )
                    )
                    if len(lb_svc) == 0:
                        self._logger.warning(
                            f"Skipping VirtualService {virtualservice.metadata.name}/{virtualservice.metadata.namespace} because no exposed service can be resolved for it"
                        )
                        continue
                    record = Record(
                        owner_id=f"{virtualservice.metadata.namespace}/{virtualservice.metadata.name}",
                        hostname=virtualservice.spec.hosts[0],
                        ip_address=lb_svc[0].status.load_balancer.ingress[0].ip,
                        port=80,
                    )
                    await self.register_record(event["type"], record)
        except UnidentifiableResourceException as ur:
            self._logger.warning(ur)
        except GatewayNotReadyException as gnre:
            self._logger.warning(gnre)
        except kubernetes.client.exceptions.ApiException as ae:
            self._logger.info("Kubernetes API error, restarting")
        except aiohttp.client_exceptions.ClientError as ce:
            self._logger.info(f"Client error while connecting to Kubernetes API: {ce}")
        except asyncio.CancelledError:
            self._logger.info("Stopping")
            self._should_stop = True
            await self._watch.close()
            raise


class HTTPRouteWatcher(BaseWatcher):
    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._api = kubernetes.client.CustomObjectsApi()

    async def run(self):
        if not await self._has_api(required_api_name="gateway.networking.k8s.io"):
            self._logger.warning(
                "Not watching for HTTPRoutes because the cluster you are connected to does not know them"
            )
            return
        self._logger.info("Watching for HTTPRoutes")
        try:
            while True:
                async for event in self._watch.stream(
                    self._api.list_cluster_custom_object,
                    "gateway.networking.k8s.io",
                    "v1",
                    "httproutes",
                ):
                    if "status" not in event["object"]:
                        self._logger.warning(
                            f"Skipping HTTPRoute {event['object']['metadata']['name']}/{event['object']['metadata']['namespace']} because it has no status yet"
                        )
                        continue
                    if "parents" not in event["object"]["status"]:
                        self._logger.warning(
                            f"Skipping HTTPRoute {event['object']['metadata']['name']}/{event['object']['metadata']['namespace']} because it has no parents"
                        )
                    httproute = HTTPRoute.model_validate(event["object"])
                    if len(httproute.status.parents) == 0:
                        self._logger.warning(
                            f"Skipping HTTPRoute {httproute.metadata.name}/{httproute.metadata.namespace} because it has no parents (yet)"
                        )
                        continue
                    if len(httproute.status.parents) > 1:
                        self._logger.warning(
                            f"HTTPRoute {httproute.metadata.name}/{httproute.metadata.namespace} has multiple gateways configured. Only the first one will be used."
                        )
                    gw_ns = httproute.status.parents[0].parentRef.namespace
                    gw_name = httproute.status.parents[0].parentRef.name
                    # Look up the gateway
                    gw_raw = await self._api.get_namespaced_custom_object(
                        group="gateway.networking.k8s.io",
                        version="v1",
                        namespace=gw_ns,
                        plural="gateways",
                        name=gw_name,
                    )
                    gw = KubernetesGateway.model_validate(gw_raw)
                    if len(gw.status.addresses) > 1:
                        self._logger.warning(
                            f"Gateway {gw_ns}/{gw} has multiple IP addresses configured. Only the first one will be used."
                        )
                    record = Record(
                        owner_id=f"{httproute.metadata.namespace}/{httproute.metadata.name}",
                        hostname=httproute.spec.hostnames[0],
                        ip_address=gw.status.addresses[0].value,
                        port=80,
                    )
                    await self.register_record(event["type"], record)
        except UnidentifiableResourceException as ur:
            self._logger.warning(ur)
        except GatewayNotReadyException as gnre:
            self._logger.warning(gnre)
        except pydantic.ValidationError as ve:
            self._logger.info("Unable to parse object")
        except kubernetes.client.exceptions.ApiException:
            self._logger.info("Kubernetes API error, restarting")
        except aiohttp.client_exceptions.ClientError as ce:
            self._logger.info(f"Client error while connecting to Kubernetes API: {ce}")
        except asyncio.CancelledError:
            self._logger.info("Stopping")
            self._should_stop = True
            await self._watch.close()
            raise
