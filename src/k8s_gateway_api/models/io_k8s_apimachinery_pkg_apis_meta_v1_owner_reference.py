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

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from typing import Optional, Set
from typing_extensions import Self

class IoK8sApimachineryPkgApisMetaV1OwnerReference(BaseModel):
    """
    OwnerReference contains enough information to let you identify an owning object. An owning object must be in the same namespace as the dependent, or be cluster-scoped, so there is no namespace field.
    """ # noqa: E501
    api_version: StrictStr = Field(description="API version of the referent.", alias="apiVersion")
    block_owner_deletion: Optional[StrictBool] = Field(default=None, description="If true, AND if the owner has the \"foregroundDeletion\" finalizer, then the owner cannot be deleted from the key-value store until this reference is removed. See https://kubernetes.io/docs/concepts/architecture/garbage-collection/#foreground-deletion for how the garbage collector interacts with this field and enforces the foreground deletion. Defaults to false. To set this field, a user needs \"delete\" permission of the owner, otherwise 422 (Unprocessable Entity) will be returned.", alias="blockOwnerDeletion")
    controller: Optional[StrictBool] = Field(default=None, description="If true, this reference points to the managing controller.")
    kind: StrictStr = Field(description="Kind of the referent. More info: https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds")
    name: StrictStr = Field(description="Name of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names#names")
    uid: StrictStr = Field(description="UID of the referent. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names#uids")
    __properties: ClassVar[List[str]] = ["apiVersion", "blockOwnerDeletion", "controller", "kind", "name", "uid"]

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
        """Create an instance of IoK8sApimachineryPkgApisMetaV1OwnerReference from a JSON string"""
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
        """Create an instance of IoK8sApimachineryPkgApisMetaV1OwnerReference from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "apiVersion": obj.get("apiVersion") if obj.get("apiVersion") is not None else '',
            "blockOwnerDeletion": obj.get("blockOwnerDeletion"),
            "controller": obj.get("controller"),
            "kind": obj.get("kind") if obj.get("kind") is not None else '',
            "name": obj.get("name") if obj.get("name") is not None else '',
            "uid": obj.get("uid") if obj.get("uid") is not None else ''
        })
        return _obj

