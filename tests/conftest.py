import typing

import pytest
import pydantic

from cloud_provider_mdns.base import Gateway, HTTPRoute, ObjectMeta, HTTPRouteSpec, \
    ParentReference, HTTPRouteStatus, RouteParentStatus, Condition, BaseNameserver, Record, \
    GatewaySpec, GatewayListenerSpec, GatewayStatus, GatewayAddresses
from tests.kubernetes_mock import KubernetesMockFactory


class TestNameserver(BaseNameserver):
    """
    A nameserver that merely records records
    """

    def __init__(self):
        super().__init__()
        self.records = set()

    async def add(self, rec: Record):
        self.records.add(rec)

    async def modify(self, rec: Record):
        self.records.add(rec)

    async def remove(self, rec: Record):
        self.records.remove(rec)


@pytest.fixture
def ns() -> TestNameserver:
    """
    Fixture for the test nameserver
    """
    return TestNameserver()


class Event(pydantic.BaseModel):
    object: HTTPRoute | Gateway
    raw_object: dict = pydantic.Field(default_factory=dict)
    type: str = pydantic.Field(default='ADDED')

@pytest.fixture()
def kubernetes(monkeypatch):
    return KubernetesMockFactory.patch_kubernetes(monkeypatch)

def create_gw(listeners: typing.List[GatewayListenerSpec] = None,
              addresses: typing.List[GatewayAddresses] = None,
              name: str = 'test-gateway',
              namespace: str = 'test') -> Gateway:
    if listeners is None:
        listeners = [GatewayListenerSpec(name='https', port=443, protocol='HTTPS')]
    if addresses is None:
        addresses = [GatewayAddresses(type='IPAddress', value='192.168.1.1')]
    return Gateway(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='Gateway',
        metadata=ObjectMeta(name=name, namespace=namespace),
        spec=GatewaySpec(listeners=listeners),
        status=GatewayStatus(addresses=addresses))

def create_ev(rec: Record = None, gw: Gateway = None, event_type: str = 'ADDED'):
    if rec is None:
        rec = Record(hostname='test.local', ip_address='172.18.0.2', port=443)
    if gw is None:
        gw = create_gw()
    return Event(object=rec.dict(),
                 raw_object=gw.model_dump(),
                 type=event_type)

def create_http_route(name: str = 'test-route',
                      namespace: str = 'test',
                      hostnames: list[str] = None,
                      parent_name: str = 'test-gw',
                      parent_namespace: str = 'test',
                      section_name: str = None,
                      port: int = None):
    if hostnames is None:
        hostnames = ['test.local']

    parent_spec = ParentReference(namespace=parent_namespace, name=parent_name)
    if section_name:
        parent_spec.sectionName = section_name
    if port:
        parent_spec.port = port

    return HTTPRoute(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='HTTPRoute',
        metadata=ObjectMeta(name=name, namespace=namespace),
        spec=HTTPRouteSpec(hostnames=hostnames, parentRefs=[parent_spec]),
        status=HTTPRouteStatus(
            parents=[RouteParentStatus(
                parentRef=ParentReference(namespace=parent_namespace, name=parent_name),
            )],
            controllerName='istio.io/gateway-controller',
            conditions=[
                Condition(type='Accepted', status=True),
                Condition(type='ResolvedRefs', status=True)
            ],
        )
    )
