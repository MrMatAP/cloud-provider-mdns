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
from typing_extensions import Annotated
from typing import Optional, Set
from typing_extensions import Self

class IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewritePath(BaseModel):
    """
    Path defines a path rewrite.  Support: Extended
    """ # noqa: E501
    replace_full_path: Optional[Annotated[str, Field(strict=True, max_length=1024)]] = Field(default=None, description="ReplaceFullPath specifies the value with which to replace the full path of a request during a rewrite or redirect.", alias="replaceFullPath")
    replace_prefix_match: Optional[Annotated[str, Field(strict=True, max_length=1024)]] = Field(default=None, description="ReplacePrefixMatch specifies the value with which to replace the prefix match of a request during a rewrite or redirect. For example, a request to \"/foo/bar\" with a prefix match of \"/foo\" and a ReplacePrefixMatch of \"/xyz\" would be modified to \"/xyz/bar\".  Note that this matches the behavior of the PathPrefix match type. This matches full path elements. A path element refers to the list of labels in the path split by the `/` separator. When specified, a trailing `/` is ignored. For example, the paths `/abc`, `/abc/`, and `/abc/def` would all match the prefix `/abc`, but the path `/abcd` would not.  ReplacePrefixMatch is only compatible with a `PathPrefix` HTTPRouteMatch. Using any other HTTPRouteMatch type on the same HTTPRouteRule will result in the implementation setting the Accepted Condition for the Route to `status: False`.  Request Path | Prefix Match | Replace Prefix | Modified Path", alias="replacePrefixMatch")
    type: StrictStr = Field(description="Type defines the type of path modifier. Additional types may be added in a future release of the API.  Note that values may be added to this enum, implementations must ensure that unknown values will not cause a crash.  Unknown values here must result in the implementation setting the Accepted Condition for the Route to `status: False`, with a Reason of `UnsupportedValue`.")
    __properties: ClassVar[List[str]] = ["replaceFullPath", "replacePrefixMatch", "type"]

    @field_validator('type')
    def type_validate_enum(cls, value):
        """Validates the enum"""
        if value not in set(['ReplaceFullPath', 'ReplacePrefixMatch']):
            raise ValueError("must be one of enum values ('ReplaceFullPath', 'ReplacePrefixMatch')")
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
        """Create an instance of IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewritePath from a JSON string"""
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
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sNetworkingGatewayV1HTTPRouteSpecRulesInnerBackendRefsInnerFiltersInnerUrlRewritePath from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "replaceFullPath": obj.get("replaceFullPath"),
            "replacePrefixMatch": obj.get("replacePrefixMatch"),
            "type": obj.get("type")
        })
        return _obj

