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

import typing

import pytest
import pydantic

from cloud_provider_mdns.base import (
    KubernetesGateway,
    HTTPRoute,
    ObjectMeta,
    HTTPRouteSpec,
    ParentReference,
    HTTPRouteStatus,
    HTTPRouteParentStatus,
    Condition,
    BaseNameserver,
    Record,
    KubernetesGatewaySpec,
    KubernetesGatewayListenerSpec,
    KubernetesGatewayStatus,
    KubernetesGatewayAddresses,
)
from cloud_provider_mdns.registry import Registry


@pytest.fixture(scope="function")
def registry():
    registry = Registry()
    assert len(registry.records()) == 0
    yield registry
    registry.clear()


@pytest.fixture(scope="function")
def gateway(registry):
    return KubernetesGateway(
        apiVersion="gateway.networking.k8s.io/v1",
        kind="Gateway",
        metadata=ObjectMeta(name="gw", namespace="edge"),
        spec=KubernetesGatewaySpec(
            listeners=[
                KubernetesGatewayListenerSpec(
                    name="https", port=443, protocol="HTTPS"
                )
            ]
        ),
        status=KubernetesGatewayStatus(
            addresses=[
                KubernetesGatewayAddresses(type="IPAddress", value="172.18.0.2")
            ]
        ),
    )


@pytest.fixture(scope="function")
def route():
    return HTTPRoute(
        apiVersion="gateway.networking.k8s.io/v1",
        kind="HTTPRoute",
        metadata=ObjectMeta(name="app-route", namespace="app"),
        spec=HTTPRouteSpec(
            hostnames=["app.local"],
            parentRefs=[ParentReference(namespace="edge", name="gw")],
        ),
        status=HTTPRouteStatus(
            parents=[
                HTTPRouteParentStatus(
                    parentRef=ParentReference(namespace="edge", name="gw"),
                    controllerName="istio.io/gateway-controller",
                    conditions=[
                        Condition(type="Accepted", status=True),
                        Condition(type="ResolvedRefs", status=True),
                    ],
                )
            ]
        ),
    )
