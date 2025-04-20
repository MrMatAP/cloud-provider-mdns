import pytest

from cloud_provider_mdns.watchers import HTTPRouteWatcher

from conftest import TestNameserver, create_gw, create_http_route

@pytest.mark.asyncio
async def test_one2one(kubernetes, ns: TestNameserver):
    """
    This tests whether a HTTPRoute binds to a single HTTP Gateway with a single IP address
    """
    gw = create_gw()
    kubernetes['custom_objects_api'].add_namespaced_custom_object(
        group='gateway.networking.k8s.io',
        version='v1',
        namespace='test',
        plural='gateways',
        name='test-route',
        obj=gw.model_dump())

    try:
        assert len(ns.records) == 0
        watcher = HTTPRouteWatcher({ns})

        route =
        await watcher.add(http_route_event.dict())

        assert len(ns.records) == 1
        rec = ns.records.pop()
        assert rec.hostname == http_route_event.object.spec.hostnames[0]
    finally:
        await ns.shutdown()
