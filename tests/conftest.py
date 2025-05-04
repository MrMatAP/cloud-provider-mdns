import typing

import pytest
import pydantic

from cloud_provider_mdns.base import Gateway, HTTPRoute, ObjectMeta, HTTPRouteSpec, \
    ParentReference, HTTPRouteStatus, RouteParentStatus, Condition, BaseNameserver, Record, \
    GatewaySpec, GatewayListenerSpec, GatewayStatus, GatewayAddresses
from cloud_provider_mdns.registry import Registry

@pytest.fixture(scope='function')
def registry():
    registry = Registry()
    assert len(registry.records()) ==0
    yield registry
    registry.clear()

@pytest.fixture(scope='function')
def gateway(registry):
    return Gateway(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='Gateway',
        metadata=ObjectMeta(name='gw', namespace='edge'),
        spec=GatewaySpec(listeners=[GatewayListenerSpec(name='https', port=443, protocol='HTTPS')]),
        status=GatewayStatus(addresses=[GatewayAddresses(type='IPAddress', value='172.18.0.2')]))

@pytest.fixture(scope='function')
def route():
    return HTTPRoute(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='HTTPRoute',
        metadata=ObjectMeta(name='app-route', namespace='app'),
        spec=HTTPRouteSpec(hostnames=['app.local'], parentRefs=[ParentReference(namespace='edge', name='gw')]),
        status=HTTPRouteStatus(
            parents=[RouteParentStatus(parentRef=ParentReference(namespace='edge', name='gw'),
                                       controllerName='istio.io/gateway-controller',
                                       conditions=[
                                           Condition(type='Accepted', status=True),
                                           Condition(type='ResolvedRefs', status=True)
                                       ])
            ]
        )
    )