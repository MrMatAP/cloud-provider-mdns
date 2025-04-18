import pytest
import asyncio

from cloud_provider_mdns.watchers import HTTPRouteWatcher

from conftest import TestNameserver
from kubernetes_mock import KubernetesMockFactory

@pytest.mark.asyncio
async def test_single_name(monkeypatch, test_gateway, test_nameserver: TestNameserver, http_route_event):
    """
    Test the HTTPRoute event
    """
    # Patch the Kubernetes API
    k8s_mocks = KubernetesMockFactory.patch_kubernetes(monkeypatch)

    # Add the Gateway to the mock API
    k8s_mocks['custom_objects_api'].add_namespaced_custom_object(
        group='gateway.networking.k8s.io',
        version='v1',
        namespace='test',
        plural='gateways',
        name='test-route',
        obj=test_gateway.dict()
    )

    try:
        watcher = HTTPRouteWatcher([test_nameserver])
        # Convert the Event object to a dictionary as expected by the watcher.add() method
        event_dict = {'object': http_route_event.object.dict(), 'type': http_route_event.type}
        await watcher.add(event_dict)
    finally:
        await test_nameserver.shutdown()

@pytest.mark.asyncio
async def test_watch_stream(mocker, monkeypatch, test_gateway, test_nameserver: TestNameserver, http_route_event):
    """
    Test the HTTPRouteWatcher.run() method with a stream of events
    """
    # Patch the Kubernetes API
    k8s_mocks = KubernetesMockFactory.patch_kubernetes(monkeypatch)

    # Mock the _has_api method to return True
    mocker.patch('cloud_provider_mdns.watchers.HTTPRouteWatcher._has_api', return_value=True)

    # Add the Gateway to the mock API
    k8s_mocks['custom_objects_api'].add_namespaced_custom_object(
        group='gateway.networking.k8s.io',
        version='v1',
        namespace='test',
        plural='gateways',
        name='test-route',
        obj=test_gateway.dict()
    )

    # Add events to the mock Watch
    k8s_mocks['watch'].add_event({
        'type': 'ADDED',
        'object': http_route_event.object.dict()
    })

    k8s_mocks['watch'].add_event({
        'type': 'MODIFIED',
        'object': http_route_event.object.dict()
    })

    try:
        # Create and start the watcher
        watcher = HTTPRouteWatcher([test_nameserver])

        # Run the watcher in a separate task
        task = asyncio.create_task(watcher.run())

        # Wait a short time for events to be processed
        await asyncio.sleep(0.1)

        # Stop the watcher
        watcher._should_stop = True

        # Wait for the task to complete
        await asyncio.wait_for(task, timeout=1.0)

        # Verify that records were added to the nameserver
        assert len(test_nameserver._records) > 0
    finally:
        await test_nameserver.shutdown()
