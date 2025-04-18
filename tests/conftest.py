import pytest
import pydantic

from cloud_provider_mdns.base import Gateway, HTTPRoute, ObjectMeta, HTTPRouteSpec, \
    ParentReference, HTTPRouteStatus, RouteParentStatus, Condition, BaseNameserver, Record, \
    GatewaySpec, GatewayListenerSpec, GatewayStatus, GatewayAddresses


class TestNameserver(BaseNameserver):
    """
    A nameserver that merely records records
    """

    def __init__(self):
        super().__init__()
        self._records = set()

    async def add(self, rec: Record):
        self._records.add(rec)

    async def modify(self, rec: Record):
        self._records.add(rec)

    async def remove(self, rec: Record):
        self._records.remove(rec)


@pytest.fixture
def test_nameserver():
    """
    Fixture for the test nameserver
    """
    ns = TestNameserver()
    yield ns


class Event(pydantic.BaseModel):
    object: HTTPRoute | Gateway
    raw_object: dict = pydantic.Field(default_factory=dict)
    type: str = pydantic.Field(default='ADDED')

@pytest.fixture
def test_gateway():
    # Create a mock Gateway for the test
    yield Gateway(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='Gateway',
        metadata=ObjectMeta(
            name='test-route',
            namespace='test'
        ),
        spec=GatewaySpec(
            listeners=[GatewayListenerSpec(
                name='https',
                port=443,
                protocol='HTTPS'
            )]
        ),
        status=GatewayStatus(
            addresses=[GatewayAddresses(
                type='IPAddress',
                value='192.168.1.1'
            )]
        )
    )

@pytest.fixture
def http_route_event():
    """
    Fixture for a HTTPRoute event
    """
    yield Event(object=HTTPRoute(
        apiVersion='gateway.networking.k8s.io/v1',
        kind='HTTPRoute',
        metadata=ObjectMeta(
            name='http-route-event',
            namespace='test'
        ),
        spec=HTTPRouteSpec(
            hostnames=['test.local'],
            parentRefs=[
                ParentReference(
                    group='gateway.networking.k8s.io',
                    kind='Gateway',
                    namespace='test',
                    name='test-route',
                    sectionName='https',
                    port=443)
            ]),
        status=HTTPRouteStatus(
            parents=[RouteParentStatus(
                parentRef=ParentReference(
                    group='gateway.networking.k8s.io',
                    kind='Gateway',
                    name='test-route',
                    namespace='test'
                ),
                controllerName='istio.io/gateway-controller',
                conditions=[
                    Condition(type='Accepted', status=True),
                    Condition(type='ResolvedRefs', status=True)
                ]
            )]
        )
    ))
