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
from k8s_gateway_api.models.io_k8s_networking_gateway_v1_http_route_spec_rules_inner_backend_refs_inner_filters_inner_url_rewrite_path import IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewritePath
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewrite(BaseModel):
    """
    URLRewrite defines a schema for a filter that modifies a request during forwarding.  Support: Extended
    """ # noqa: E501
    hostname: Optional[Annotated[str, Field(min_length=1, strict=True, max_length=253)]] = Field(default=None, description="Hostname is the value to be used to replace the Host header value during forwarding.  Support: Extended")
    path: Optional[IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewritePath] = None
    __properties: ClassVar[List[str]] = ["hostname", "path"]

    @field_validator('hostname')
    def hostname_validate_regular_expression(cls, value):
        """Validates the regular expression"""
        if value is None:
            return value

        if not re.match(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$", value):
            raise ValueError(r"must validate the regular expression /^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$/")
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
        """Create an instance of IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewrite from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of path
        if self.path:
            _dict['path'] = self.path.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewrite from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "hostname": obj.get("hostname"),
            "path": IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewritePath.from_dict(obj["path"]) if obj.get("path") is not None else None
        })
        return _obj


