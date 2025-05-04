import pytest

from cloud_provider_mdns.base import ParentReference, GatewayListenerSpec


@pytest.mark.asyncio
async def test_registry_one2one(registry, gateway, route):
    """
    This test verifies basic registry functionality for a single gateway and route.
    It checks that adding a gateway alone creates no records, adding a route creates
    one record, and removing the route removes the record from the registry.
    """
    await registry.add_gateway(gateway)
    assert len(registry.records()) == 0
    await registry.add_route(route)
    assert len(registry.records()) == 1
    await registry.remove_route(route)
    assert len(registry.records()) == 0

@pytest.mark.asyncio
async def test_registry_one2one_gw_disappears(registry, gateway, route):
    """
    This test verifies that when a gateway is removed, all associated route records 
    are also removed from the registry, even if the routes themselves still exist. The test 
    creates a gateway and route, adds them to registry, then removes the gateway to ensure 
    cleanup occurs properly.
    """
    await registry.add_gateway(gateway)
    assert len(registry.records()) == 0
    await registry.add_route(route)
    assert len(registry.records()) == 1
    await registry.remove_gateway(gateway)
    assert len(registry.records()) == 0

@pytest.mark.asyncio
async def test_registry_many2one(registry, gateway, route):
    """
    This test verifies that adding routes incrementally increases records depending on the number
    of hostnames to a single gateway.
    It also tests that all the routes bound to a single gateway are removed when the gateway is removed.
    """
    app1 = route.model_copy(deep=True)
    app1.metadata.name = 'app1'
    app1.spec.hostnames = ['app1.local']
    app2 = route.model_copy(deep=True)
    app2.metadata.name = 'app2'
    app2.spec.hostnames = ['app2.local', 'app2.test.org']
    app3 = route.model_copy(deep=True)
    app3.metadata.name = 'app3'
    app3.spec.hostnames = ['app3.local', 'app3.test.org']

    await registry.add_gateway(gateway)
    assert len(registry.records()) == 0
    await registry.add_route(app1)
    assert len(registry.records()) == 1
    await registry.add_route(app2)
    assert len(registry.records()) == 3
    await registry.add_route(app3)
    assert len(registry.records()) == 5

    await registry.remove_route(app1)
    assert len(registry.records()) == 4

    await registry.remove_gateway(gateway)
    assert len(registry.records()) == 0

@pytest.mark.asyncio
async def test_registry_update_route(registry, gateway, route):
    app1 = route.model_copy(deep=True)
    app1.metadata.name = 'app1'
    app1.spec.hostnames = ['app1.local']

    await registry.add_gateway(gateway)
    assert len(registry.records()) == 0
    await registry.add_route(app1)
    assert len(registry.records()) == 1

    app1.spec.hostnames = ['app1.local', 'app1.test.org']
    await registry.add_route(app1)
    assert len(registry.records()) == 2

@pytest.mark.asyncio
async def test_route_many2many(registry, gateway, route):
    gw1 = gateway.model_copy(deep=True)
    gw1.metadata.name = 'gw1'
    gw2 = gateway.model_copy(deep=True)
    gw2.metadata.name = 'gw2'

    app1 = route.model_copy(deep=True)
    app1.metadata.name = 'app1'
    app1.spec.hostnames = ['app1.local', 'app1.test.org']
    app1.spec.parentRefs = [
        ParentReference(namespace=gw1.metadata.namespace, name=gw1.metadata.name),
        ParentReference(namespace=gw2.metadata.namespace, name=gw2.metadata.name)
    ]

    await registry.add_gateway(gw1)
    await registry.add_gateway(gw2)
    assert len(registry.records()) == 0
    await registry.add_route(app1)
    assert len(registry.records()) == 4

    await registry.remove_gateway(gw1)
    assert len(registry.records()) == 2
