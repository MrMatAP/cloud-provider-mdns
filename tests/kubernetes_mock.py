"""
Mock implementations for the Kubernetes API.
This module provides mock implementations for the Kubernetes API classes used in the cloud-provider-mdns project.
"""
import asyncio
from typing import Dict, List, Any, Callable, AsyncGenerator, Optional, Set
from unittest.mock import MagicMock

import kubernetes_asyncio as kubernetes
from kubernetes_asyncio.client import ApiClient, CustomObjectsApi, NetworkingV1Api, V1APIGroupList, V1APIGroup


class MockApiGroup:
    def __init__(self, name: str):
        self.name = name


class MockApiGroupList:
    def __init__(self, groups: List[MockApiGroup]):
        self.groups = groups


class MockApisApi:
    """Mock implementation of the Kubernetes ApisApi."""
    
    def __init__(self, available_apis: Optional[Set[str]] = None):
        self.available_apis = available_apis or {"gateway.networking.k8s.io", "networking.k8s.io"}
    
    async def get_api_versions(self) -> V1APIGroupList:
        """Return a mock API group list with the configured available APIs."""
        groups = [V1APIGroup(name=api) for api in self.available_apis]
        return V1APIGroupList(groups=groups)


class MockWatch:
    """Mock implementation of the Kubernetes Watch."""
    
    def __init__(self):
        self.events = []
        self.stopped = False
    
    def add_event(self, event: Dict[str, Any]):
        """Add an event to the watch stream."""
        self.events.append(event)
    
    def stop(self):
        """Stop the watch stream."""
        self.stopped = True
    
    async def close(self):
        """Close the watch stream."""
        self.stopped = True
    
    async def stream(self, func: Callable, *args, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream events from the watch."""
        for event in self.events:
            if self.stopped:
                break
            yield event
            # Add a small delay to simulate real-world behavior
            await asyncio.sleep(0.01)


class MockCustomObjectsApi:
    """Mock implementation of the Kubernetes CustomObjectsApi."""
    
    def __init__(self):
        self.objects = {}  # Dict to store custom objects by (group, version, namespace, plural, name)
    
    def add_namespaced_custom_object(self, group: str, version: str, namespace: str, plural: str, name: str, obj: Dict[str, Any]):
        """Add a custom object to the mock API."""
        key = (group, version, namespace, plural, name)
        self.objects[key] = obj
    
    async def get_namespaced_custom_object(self, group: str, version: str, namespace: str, plural: str, name: str) -> Dict[str, Any]:
        """Get a custom object from the mock API."""
        key = (group, version, namespace, plural, name)
        if key not in self.objects:
            raise kubernetes.client.exceptions.ApiException(status=404, reason=f"Not Found: {key}")
        return self.objects[key]
    
    async def list_cluster_custom_object(self, group: str, version: str, plural: str) -> Dict[str, Any]:
        """List custom objects from the mock API."""
        items = []
        for (g, v, _, p, _), obj in self.objects.items():
            if g == group and v == version and p == plural:
                items.append(obj)
        return {"items": items}


class MockNetworkingV1Api:
    """Mock implementation of the Kubernetes NetworkingV1Api."""
    
    def __init__(self):
        self.ingresses = []
    
    def add_ingress(self, ingress: Dict[str, Any]):
        """Add an ingress to the mock API."""
        self.ingresses.append(ingress)
    
    async def list_ingress_for_all_namespaces(self) -> Dict[str, Any]:
        """List ingresses from the mock API."""
        return {"items": self.ingresses}


class KubernetesMockFactory:
    """Factory for creating Kubernetes mock objects."""
    
    @staticmethod
    def create_apis_api(available_apis: Optional[Set[str]] = None) -> MockApisApi:
        """Create a mock ApisApi."""
        return MockApisApi(available_apis)
    
    @staticmethod
    def create_custom_objects_api() -> MockCustomObjectsApi:
        """Create a mock CustomObjectsApi."""
        return MockCustomObjectsApi()
    
    @staticmethod
    def create_networking_v1_api() -> MockNetworkingV1Api:
        """Create a mock NetworkingV1Api."""
        return MockNetworkingV1Api()
    
    @staticmethod
    def create_watch() -> MockWatch:
        """Create a mock Watch."""
        return MockWatch()
    
    @staticmethod
    def patch_kubernetes(monkeypatch) -> dict[str, MockApisApi | MockCustomObjectsApi | MockNetworkingV1Api | MockWatch | MagicMock]:
        """Patch the kubernetes_asyncio module with mock implementations."""
        # Create mock instances
        mock_apis_api = KubernetesMockFactory.create_apis_api()
        mock_custom_objects_api = KubernetesMockFactory.create_custom_objects_api()
        mock_networking_v1_api = KubernetesMockFactory.create_networking_v1_api()
        mock_watch = KubernetesMockFactory.create_watch()
        
        # Create a mock ApiClient
        mock_api_client = MagicMock(spec=ApiClient)
        
        # Patch the kubernetes module
        monkeypatch.setattr(kubernetes.client, "ApisApi", lambda: mock_apis_api)
        monkeypatch.setattr(kubernetes.client, "CustomObjectsApi", lambda: mock_custom_objects_api)
        monkeypatch.setattr(kubernetes.client, "NetworkingV1Api", lambda: mock_networking_v1_api)
        monkeypatch.setattr(kubernetes.client, "ApiClient", lambda: mock_api_client)
        monkeypatch.setattr(kubernetes.watch, "Watch", lambda: mock_watch)
        
        return {
            "apis_api": mock_apis_api,
            "custom_objects_api": mock_custom_objects_api,
            "networking_v1_api": mock_networking_v1_api,
            "watch": mock_watch,
            "api_client": mock_api_client
        }