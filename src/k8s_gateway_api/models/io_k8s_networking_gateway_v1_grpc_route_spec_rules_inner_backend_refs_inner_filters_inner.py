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

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List, Optional
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_backend_refs_inner_filters_inner_extension_ref import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerExtensionRef
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_backend_refs_inner_filters_inner_request_header_modifier import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifier
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_backend_refs_inner_filters_inner_request_mirror import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestMirror
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_backend_refs_inner_filters_inner_response_header_modifier import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerResponseHeaderModifier
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInner(BaseModel):
    """
    GRPCRouteFilter defines processing steps that must be completed during the request or response lifecycle. GRPCRouteFilters are meant as an extension point to express processing that may be done in Gateway implementations. Some examples include request or response modification, implementing authentication strategies, rate-limiting, and traffic shaping. API guarantee/conformance is defined based on the type of the filter.
    """ # noqa: E501
    extension_ref: Optional[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerExtensionRef] = Field(default=None, alias="extensionRef")
    request_header_modifier: Optional[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifier] = Field(default=None, alias="requestHeaderModifier")
    request_mirror: Optional[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestMirror] = Field(default=None, alias="requestMirror")
    response_header_modifier: Optional[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerResponseHeaderModifier] = Field(default=None, alias="responseHeaderModifier")
    type: StrictStr = Field(description="Type identifies the type of filter to apply. As with other API fields, types are classified into three conformance levels:  - Core: Filter types and their corresponding configuration defined by   \"Support: Core\" in this package, e.g. \"RequestHeaderModifier\". All   implementations supporting GRPCRoute MUST support core filters.  - Extended: Filter types and their corresponding configuration defined by   \"Support: Extended\" in this package, e.g. \"RequestMirror\". Implementers   are encouraged to support extended filters.  - Implementation-specific: Filters that are defined and supported by specific vendors.   In the future, filters showing convergence in behavior across multiple   implementations will be considered for inclusion in extended or core   conformance levels. Filter-specific configuration for such filters   is specified using the ExtensionRef field. `Type` MUST be set to   \"ExtensionRef\" for custom filters.  Implementers are encouraged to define custom implementation types to extend the core API with implementation-specific behavior.  If a reference to a custom filter type cannot be resolved, the filter MUST NOT be skipped. Instead, requests that would have been processed by that filter MUST receive a HTTP error response.  ")
    __properties: ClassVar[List[str]] = ["extensionRef", "requestHeaderModifier", "requestMirror", "responseHeaderModifier", "type"]

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['ResponseHeaderModifier', 'RequestHeaderModifier', 'RequestMirror', 'ExtensionRef']):
            raise ValueError("must be one of enum values ('ResponseHeaderModifier', 'RequestHeaderModifier', 'RequestMirror', 'ExtensionRef')")
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
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInner from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of extension_ref
        if self.extension_ref:
            _dict['extensionRef'] = self.extension_ref.to_dict()
        # override the default output from pydantic by calling `to_dict()` of request_header_modifier
        if self.request_header_modifier:
            _dict['requestHeaderModifier'] = self.request_header_modifier.to_dict()
        # override the default output from pydantic by calling `to_dict()` of request_mirror
        if self.request_mirror:
            _dict['requestMirror'] = self.request_mirror.to_dict()
        # override the default output from pydantic by calling `to_dict()` of response_header_modifier
        if self.response_header_modifier:
            _dict['responseHeaderModifier'] = self.response_header_modifier.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInner from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "extensionRef": IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerExtensionRef.from_dict(obj["extensionRef"]) if obj.get("extensionRef") is not None else None,
            "requestHeaderModifier": IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifier.from_dict(obj["requestHeaderModifier"]) if obj.get("requestHeaderModifier") is not None else None,
            "requestMirror": IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestMirror.from_dict(obj["requestMirror"]) if obj.get("requestMirror") is not None else None,
            "responseHeaderModifier": IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerResponseHeaderModifier.from_dict(obj["responseHeaderModifier"]) if obj.get("responseHeaderModifier") is not None else None,
            "type": obj.get("type")
        })
        return _obj

