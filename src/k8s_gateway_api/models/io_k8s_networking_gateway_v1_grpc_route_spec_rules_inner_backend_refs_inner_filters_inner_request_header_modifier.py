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

from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Annotated
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_backend_refs_inner_filters_inner_request_header_modifier_add_inner import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifierAddInner
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifier(BaseModel):
    """
    RequestHeaderModifier defines a schema for a filter that modifies request headers.  Support: Core
    """ # noqa: E501
    add: Optional[Annotated[List[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifierAddInner], Field(max_length=16)]] = Field(default=None, description="Add adds the given header(s) (name, value) to the request before the action. It appends to any existing values associated with the header name.  Input:   GET /foo HTTP/1.1   my-header: foo  Config:   add:   - name: \"my-header\"     value: \"bar,baz\"  Output:   GET /foo HTTP/1.1   my-header: foo,bar,baz")
    remove: Optional[Annotated[List[StrictStr], Field(max_length=16)]] = Field(default=None, description="Remove the given header(s) from the HTTP request before the action. The value of Remove is a list of HTTP header names. Note that the header names are case-insensitive (see https://datatracker.ietf.org/doc/html/rfc2616#section-4.2).  Input:   GET /foo HTTP/1.1   my-header1: foo   my-header2: bar   my-header3: baz  Config:   remove: [\"my-header1\", \"my-header3\"]  Output:   GET /foo HTTP/1.1   my-header2: bar")
    set: Optional[Annotated[List[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifierAddInner], Field(max_length=16)]] = Field(default=None, description="Set overwrites the request with the given header (name, value) before the action.  Input:   GET /foo HTTP/1.1   my-header: foo  Config:   set:   - name: \"my-header\"     value: \"bar\"  Output:   GET /foo HTTP/1.1   my-header: bar")
    __properties: ClassVar[List[str]] = ["add", "remove", "set"]

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
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifier from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in add (list)
        _items = []
        if self.add:
            for _item_add in self.add:
                if _item_add:
                    _items.append(_item_add.to_dict())
            _dict['add'] = _items
        # override the default output from pydantic by calling `to_dict()` of each item in set (list)
        _items = []
        if self.set:
            for _item_set in self.set:
                if _item_set:
                    _items.append(_item_set.to_dict())
            _dict['set'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifier from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "add": [IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifierAddInner.from_dict(_item) for _item in obj["add"]] if obj.get("add") is not None else None,
            "remove": obj.get("remove"),
            "set": [IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerBackendRefsInnerFiltersInnerRequestHeaderModifierAddInner.from_dict(_item) for _item in obj["set"]] if obj.get("set") is not None else None
        })
        return _obj

