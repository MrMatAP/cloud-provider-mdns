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

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from k8s_gateway_api.models.io_k8s_apimachinery_pkg_apis_meta_v1_list_meta import IoK8sApimachineryPkgApisMetaV1ListMeta
from k8s_gateway_api.models.io_k8s_apimachinery_pkg_apis_meta_v1_status_details import IoK8sApimachineryPkgApisMetaV1StatusDetails
from typing import Optional, Set
from typing_extensions import Self

class IoK8sApimachineryPkgApisMetaV1Status(BaseModel):
    """
    Status is a return value for calls that don't return other objects.
    """ # noqa: E501
    api_version: Optional[StrictStr] = Field(default=None, description="APIVersion defines the versioned schema of this representation of an object. Servers should convert recognized schemas to the latest internal value, and may reject unrecognized values. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#resources", alias="apiVersion")
    code: Optional[StrictInt] = Field(default=None, description="Suggested HTTP return code for this status, 0 if not set.")
    details: Optional[IoK8sApimachineryPkgApisMetaV1StatusDetails] = Field(default=None, description="Extended data associated with the reason.  Each reason may define its own extended details. This field is optional and the data returned is not guaranteed to conform to any schema except that defined by the reason type.")
    kind: Optional[StrictStr] = Field(default=None, description="Kind is a string value representing the REST resource this object represents. Servers may infer this from the endpoint the client submits requests to. Cannot be updated. In CamelCase. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds")
    message: Optional[StrictStr] = Field(default=None, description="A human-readable description of the status of this operation.")
    metadata: Optional[IoK8sApimachineryPkgApisMetaV1ListMeta] = Field(default=None, description="Standard list metadata. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds")
    reason: Optional[StrictStr] = Field(default=None, description="A machine-readable description of why this operation is in the \"Failure\" status. If this value is empty there is no information available. A Reason clarifies an HTTP status code but does not override it.")
    status: Optional[StrictStr] = Field(default=None, description="Status of the operation. One of: \"Success\" or \"Failure\". More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status")
    __properties: ClassVar[List[str]] = ["apiVersion", "code", "details", "kind", "message", "metadata", "reason", "status"]

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
        """Create an instance of IoK8sApimachineryPkgApisMetaV1Status from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of details
        if self.details:
            _dict['details'] = self.details.to_dict()
        # override the default output from pydantic by calling `to_dict()` of metadata
        if self.metadata:
            _dict['metadata'] = self.metadata.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of IoK8sApimachineryPkgApisMetaV1Status from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "apiVersion": obj.get("apiVersion"),
            "code": obj.get("code"),
            "details": IoK8sApimachineryPkgApisMetaV1StatusDetails.from_dict(obj["details"]) if obj.get("details") is not None else None,
            "kind": obj.get("kind"),
            "message": obj.get("message"),
            "metadata": IoK8sApimachineryPkgApisMetaV1ListMeta.from_dict(obj["metadata"]) if obj.get("metadata") is not None else None,
            "reason": obj.get("reason"),
            "status": obj.get("status")
        })
        return _obj

