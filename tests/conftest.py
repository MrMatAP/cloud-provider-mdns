import typing

import pytest
import pydantic

from cloud_provider_mdns.base import KubernetesGateway, HTTPRoute, ObjectMeta, HTTPRouteSpec, \
    ParentReference, HTTPRouteStatus, HTTPRouteParentStatus, Condition, BaseNameserver, Record, \
    KubernetesGatewaySpec, KubernetesGatewayListenerSpec, KubernetesGatewayStatus, KubernetesGatewayAddresses
from cloud_provider_mdns.registry import Registry

@pytest.fixture(scope='function')
def registry():
    registry = Registry()
    assert len(registry.records()) ==0
    yield registry
    registry.clear()

@pytest.fixture(scope='function')
def gateway(registry):
    return KubernetesGateway(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='Gateway',
        metadata=ObjectMeta(name='gw', namespace='edge'),
        spec=KubernetesGatewaySpec(listeners=[KubernetesGatewayListenerSpec(name='https', port=443, protocol='HTTPS')]),
        status=KubernetesGatewayStatus(addresses=[KubernetesGatewayAddresses(type='IPAddress', value='172.18.0.2')]))

@pytest.fixture(scope='function')
def route():
    return HTTPRoute(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='HTTPRoute',
        metadata=ObjectMeta(name='app-route', namespace='app'),
        spec=HTTPRouteSpec(hostnames=['app.local'], parentRefs=[ParentReference(namespace='edge', name='gw')]),
        status=HTTPRouteStatus(
            parents=[HTTPRouteParentStatus(parentRef=ParentReference(namespace='edge', name='gw'),
                                           controllerName='istio.io/gateway-controller',
                                           conditions=[
                                           Condition(type='Accepted', status=True),
                                           Condition(type='ResolvedRefs', status=True)
                                       ])
                     ]
        )
    )