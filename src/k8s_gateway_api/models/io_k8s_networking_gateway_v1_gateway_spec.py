# coding: utf-8

"""
    Kubernetes CRD Swagger

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: v0.1.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_gateway_spec_addresses_inner import IoK8sNetworkingGatewayV1GatewaySpecAddressesInner
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_gateway_spec_infrastructure import IoK8sNetworkingGatewayV1GatewaySpecInfrastructure
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_gateway_spec_listeners_inner import IoK8sNetworkingGatewayV1GatewaySpecListenersInner
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1GatewaySpec(BaseModel):
    """
    Spec defines the desired state of Gateway.
    """ # noqa: E501
    addresses: Optional[Annotated[List[IoK8sNetworkingGatewayV1GatewaySpecAddressesInner], Field(max_length=16)]] = Field(default=None, description="Addresses requested for this Gateway. This is optional and behavior can depend on the implementation. If a value is set in the spec and the requested address is invalid or unavailable, the implementation MUST indicate this in the associated entry in GatewayStatus.Addresses.  The Addresses field represents a request for the address(es) on the \"outside of the Gateway\", that traffic bound for this Gateway will use. This could be the IP address or hostname of an external load balancer or other networking infrastructure, or some other address that traffic will be sent to.  If no Addresses are specified, the implementation MAY schedule the Gateway in an implementation-specific manner, assigning an appropriate set of Addresses.  The implementation MUST bind all Listeners to every GatewayAddress that it assigns to the Gateway and add a corresponding entry in GatewayStatus.Addresses.  Support: Extended  ")
    gateway_class_name: Annotated[str, Field(min_length=1, strict=True, max_length=253)] = Field(description="GatewayClassName used for this Gateway. This is the name of a GatewayClass resource.", alias="gatewayClassName")
    infrastructure: Optional[IoK8sNetworkingGatewayV1GatewaySpecInfrastructure] = None
    listeners: Annotated[List[IoK8sNetworkingGatewayV1GatewaySpecListenersInner], Field(min_length=1, max_length=64)] = Field(description="Listeners associated with this Gateway. Listeners define logical endpoints that are bound on this Gateway's addresses. At least one Listener MUST be specified.  Each Listener in a set of Listeners (for example, in a single Gateway) MUST be _distinct_, in that a traffic flow MUST be able to be assigned to exactly one listener. (This section uses \"set of Listeners\" rather than \"Listeners in a single Gateway\" because implementations MAY merge configuration from multiple Gateways onto a single data plane, and these rules _also_ apply in that case).  Practically, this means that each listener in a set MUST have a unique combination of Port, Protocol, and, if supported by the protocol, Hostname.  Some combinations of port, protocol, and TLS settings are considered Core support and MUST be supported by implementations based on their targeted conformance profile:  HTTP Profile  1. HTTPRoute, Port: 80, Protocol: HTTP 2. HTTPRoute, Port: 443, Protocol: HTTPS, TLS Mode: Terminate, TLS keypair provided  TLS Profile  1. TLSRoute, Port: 443, Protocol: TLS, TLS Mode: Passthrough  \"Distinct\" Listeners have the following property:  The implementation can match inbound requests to a single distinct Listener. When multiple Listeners share values for fields (for example, two Listeners with the same Port value), the implementation can match requests to only one of the Listeners using other Listener fields.  For example, the following Listener scenarios are distinct:  1. Multiple Listeners with the same Port that all use the \"HTTP\"    Protocol that all have unique Hostname values. 2. Multiple Listeners with the same Port that use either the \"HTTPS\" or    \"TLS\" Protocol that all have unique Hostname values. 3. A mixture of \"TCP\" and \"UDP\" Protocol Listeners, where no Listener    with the same Protocol has the same Port value.  Some fields in the Listener struct have possible values that affect whether the Listener is distinct. Hostname is particularly relevant for HTTP or HTTPS protocols.  When using the Hostname value to select between same-Port, same-Protocol Listeners, the Hostname value must be different on each Listener for the Listener to be distinct.  When the Listeners are distinct based on Hostname, inbound request hostnames MUST match from the most specific to least specific Hostname values to choose the correct Listener and its associated set of Routes.  Exact matches must be processed before wildcard matches, and wildcard matches must be processed before fallback (empty Hostname value) matches. For example, `\"foo.example.com\"` takes precedence over `\"*.example.com\"`, and `\"*.example.com\"` takes precedence over `\"\"`.  Additionally, if there are multiple wildcard entries, more specific wildcard entries must be processed before less specific wildcard entries. For example, `\"*.foo.example.com\"` takes precedence over `\"*.example.com\"`. The precise definition here is that the higher the number of dots in the hostname to the right of the wildcard character, the higher the precedence.  The wildcard character will match any number of characters _and dots_ to the left, however, so `\"*.example.com\"` will match both `\"foo.bar.example.com\"` _and_ `\"bar.example.com\"`.  If a set of Listeners contains Listeners that are not distinct, then those Listeners are Conflicted, and the implementation MUST set the \"Conflicted\" condition in the Listener Status to \"True\".  Implementations MAY choose to accept a Gateway with some Conflicted Listeners only if they only accept the partial Listener set that contains no Conflicted Listeners. To put this another way, implementations may accept a partial Listener set only if they throw out *all* the conflicting Listeners. No picking one of the conflicting listeners as the winner. This also means that the Gateway must have at least one non-conflicting Listener in this case, otherwise it violates the requirement that at least one Listener must be present.  The implementation MUST set a \"ListenersNotValid\" condition on the Gateway Status when the Gateway contains Conflicted Listeners whether or not they accept the Gateway. That Condition SHOULD clearly indicate in the Message which Listeners are conflicted, and which are Accepted. Additionally, the Listener status for those listeners SHOULD indicate which Listeners are conflicted and not Accepted.  A Gateway's Listeners are considered \"compatible\" if:  1. They are distinct. 2. The implementation can serve them in compliance with the Addresses    requirement that all Listeners are available on all assigned    addresses.  Compatible combinations in Extended support are expected to vary across implementations. A combination that is compatible for one implementation may not be compatible for another.  For example, an implementation that cannot serve both TCP and UDP listeners on the same address, or cannot mix HTTPS and generic TLS listens on the same port would not consider those cases compatible, even though they are distinct.  Note that requests SHOULD match at most one Listener. For example, if Listeners are defined for \"foo.example.com\" and \"*.example.com\", a request to \"foo.example.com\" SHOULD only be routed using routes attached to the \"foo.example.com\" Listener (and not the \"*.example.com\" Listener). This concept is known as \"Listener Isolation\". Implementations that do not support Listener Isolation MUST clearly document this.  Implementations MAY merge separate Gateways onto a single set of Addresses if all Listeners across all Gateways are compatible.  Support: Core")
    __properties: ClassVar[List[str]] = ["addresses", "gatewayClassName", "infrastructure", "listeners"]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        protected_namespaces=(),
    )


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1GatewaySpec from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        excluded_fields: Set[str] = set([
        ])

        _dict = self.model_dump(
            by_alias=True,
            exclude=excluded_fields,
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of each item in addresses (list)
        _items = []
        if self.addresses:
            for _item_addresses in self.addresses:
                if _item_addresses:
                    _items.append(_item_addresses.to_dict())
            _dict['addresses'] = _items
        # override the default output from pydantic by calling `to_dict()` of infrastructure
        if self.infrastructure:
            _dict['infrastructure'] = self.infrastructure.to_dict()
        # override the default output from pydantic by calling `to_dict()` of each item in listeners (list)
        _items = []
        if self.listeners:
            for _item_listeners in self.listeners:
                if _item_listeners:
                    _items.append(_item_listeners.to_dict())
            _dict['listeners'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1GatewaySpec from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "addresses": [IoK8sNetworkingGatewayV1GatewaySpecAddressesInner.from_dict(_item) for _item in obj["addresses"]] if obj.get("addresses") is not None else None,
            "gatewayClassName": obj.get("gatewayClassName"),
            "infrastructure": IoK8sNetworkingGatewayV1GatewaySpecInfrastructure.from_dict(obj["infrastructure"]) if obj.get("infrastructure") is not None else None,
            "listeners": [IoK8sNetworkingGatewayV1GatewaySpecListenersInner.from_dict(_item) for _item in obj["listeners"]] if obj.get("listeners") is not None else None
        })
        return _obj

