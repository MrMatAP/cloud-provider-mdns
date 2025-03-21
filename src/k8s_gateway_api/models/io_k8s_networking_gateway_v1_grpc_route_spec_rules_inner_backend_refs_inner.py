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

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_backend_refs_inner_filters_inner import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInner
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInner(BaseModel):
    """
    GRPCBackendRef defines how a GRPCRoute forwards a gRPC request.  Note that when a namespace different than the local namespace is specified, a ReferenceGrant object is required in the referent namespace to allow that namespace's owner to accept the reference. See the ReferenceGrant documentation for details.  <gateway:experimental:description>  When the BackendRef points to a Kubernetes Service, implementations SHOULD honor the appProtocol field if it is set for the target Service Port.  Implementations supporting appProtocol SHOULD recognize the Kubernetes Standard Application Protocols defined in KEP-3726.  If a Service appProtocol isn't specified, an implementation MAY infer the backend protocol through its own means. Implementations MAY infer the protocol from the Route type referring to the backend Service.  If a Route is not able to send traffic to the backend using the specified protocol then the backend is considered invalid. Implementations MUST set the \"ResolvedRefs\" condition to \"False\" with the \"UnsupportedProtocol\" reason.  </gateway:experimental:description>
    """ # noqa: E501
    filters: Optional[Annotated[List[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInner], Field(max_length=16)]] = Field(default=None, description="Filters defined at this level MUST be executed if and only if the request is being forwarded to the backend defined here.  Support: Implementation-specific (For broader support of filters, use the Filters field in GRPCRouteRule.)")
    group: Optional[Annotated[str, Field(strict=True, max_length=253)]] = Field(default='', description="Group is the group of the referent. For example, \"gateway.networking.k8s.io\". When unspecified or empty string, core API group is inferred.")
    kind: Optional[Annotated[str, Field(min_length=1, strict=True, max_length=63)]] = Field(default='Service', description="Kind is the Kubernetes resource kind of the referent. For example \"Service\".  Defaults to \"Service\" when not specified.  ExternalName services can refer to CNAME DNS records that may live outside of the cluster and as such are difficult to reason about in terms of conformance. They also may not be safe to forward to (see CVE-2021-25740 for more information). Implementations SHOULD NOT support ExternalName Services.  Support: Core (Services with a type other than ExternalName)  Support: Implementation-specific (Services with type ExternalName)")
    name: Annotated[str, Field(min_length=1, strict=True, max_length=253)] = Field(description="Name is the name of the referent.")
    namespace: Optional[Annotated[str, Field(min_length=1, strict=True, max_length=63)]] = Field(default=None, description="Namespace is the namespace of the backend. When unspecified, the local namespace is inferred.  Note that when a namespace different than the local namespace is specified, a ReferenceGrant object is required in the referent namespace to allow that namespace's owner to accept the reference. See the ReferenceGrant documentation for details.  Support: Core")
    port: Optional[Annotated[int, Field(le=65535, strict=True, ge=1)]] = Field(default=None, description="Port specifies the destination port number to use for this resource. Port is required when the referent is a Kubernetes Service. In this case, the port number is the service port number, not the target port. For other resources, destination port might be derived from the referent resource or this field.")
    weight: Optional[Annotated[int, Field(le=1000000, strict=True, ge=0)]] = Field(default=1, description="Weight specifies the proportion of requests forwarded to the referenced backend. This is computed as weight/(sum of all weights in this BackendRefs list). For non-zero values, there may be some epsilon from the exact proportion defined here depending on the precision an implementation supports. Weight is not a percentage and the sum of weights does not need to equal 100.  If only one backend is specified and it has a weight greater than 0, 100% of the traffic is forwarded to that backend. If weight is set to 0, no traffic should be forwarded for this entry. If unspecified, weight defaults to 1.  Support for this field varies based on the context where used.")
    __properties: ClassVar[List[str]] = ["filters", "group", "kind", "name", "namespace", "port", "weight"]

    @field_validator('group')
    def group_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if not re.match(r"^$|^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$", value):
            raise ValueError(r"must validate the regular expression /^$|^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$/")
        return value

    @field_validator('kind')
    def kind_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if not re.match(r"^[a-zA-Z]([-a-zA-Z0-9]*[a-zA-Z0-9])?$", value):
            raise ValueError(r"must validate the regular expression /^[a-zA-Z]([-a-zA-Z0-9]*[a-zA-Z0-9])?$/")
        return value

    @field_validator('namespace')
    def namespace_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", value):
            raise ValueError(r"must validate the regular expression /^[a-z0-9]([-a-z0-9]*[a-z0-9])?$/")
        return value

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
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInner from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in filters (list)
        _items = []
        if self.filters:
            for _item_filters in self.filters:
                if _item_filters:
                    _items.append(_item_filters.to_dict())
            _dict['filters'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInner from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "filters": [IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInner.from_dict(_item) for _item in obj["filters"]] if obj.get("filters") is not None else None,
            "group": obj.get("group") if obj.get("group") is not None else '',
            "kind": obj.get("kind") if obj.get("kind") is not None else 'Service',
            "name": obj.get("name"),
            "namespace": obj.get("namespace"),
            "port": obj.get("port"),
            "weight": obj.get("weight") if obj.get("weight") is not None else 1
        })
        return _obj


