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
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_matches_inner_headers_inner import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInnerHeadersInner
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_grpc_route_spec_rules_inner_matches_inner_method import IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInnerMethod
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInner(BaseModel):
    """
    GRPCRouteMatch defines the predicate used to match requests to a given action. Multiple match types are ANDed together, i.e. the match will evaluate to true only if all conditions are satisfied.  For example, the match below will match a gRPC request only if its service is `foo` AND it contains the `version: v1` header:  ``` matches:   - method:     type: Exact     service: \"foo\"     headers:   - name: \"version\"     value \"v1\"  ```
    """ # noqa: E501
    headers: Optional[Annotated[List[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInnerHeadersInner], Field(max_length=16)]] = Field(default=None, description="Headers specifies gRPC request header matchers. Multiple match values are ANDed together, meaning, a request MUST match all the specified headers to select the route.")
    method: Optional[IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInnerMethod] = None
    __properties: ClassVar[List[str]] = ["headers", "method"]

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
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInner from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of each item in headers (list)
        _items = []
        if self.headers:
            for _item_headers in self.headers:
                if _item_headers:
                    _items.append(_item_headers.to_dict())
            _dict['headers'] = _items
        # override the default output from pydantic by calling `to_dict()` of method
        if self.method:
            _dict['method'] = self.method.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInner from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "headers": [IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInnerHeadersInner.from_dict(_item) for _item in obj["headers"]] if obj.get("headers") is not None else None,
            "method": IoK8sNetworkingGatewayV1GRPCRouteSpecRulesInnerMatchesInnerMethod.from_dict(obj["method"]) if obj.get("method") is not None else None
        })
        return _obj

