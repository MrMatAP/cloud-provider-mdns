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

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from typing import Optional, Set
from typing_extensions import Self

class IoK8sApimachineryPkgApisMetaV1ManagedFieldsEntry(BaseModel):
    """
    ManagedFieldsEntry is a workflow-id, a FieldSet and the group version of the resource that the fieldset applies to.
    """ # noqa: E501
    api_version: Optional[StrictStr] = Field(default=None, description="APIVersion defines the version of this resource that this field set applies to. The format is \"group/version\" just like the top-level APIVersion field. It is necessary to track the version of a field set because it cannot be automatically converted.", alias="apiVersion")
    fields_type: Optional[StrictStr] = Field(default=None, description="FieldsType is the discriminator for the different fields format and version. There is currently only one possible value: \"FieldsV1\"", alias="fieldsType")
    fields_v1: Optional[Dict[str, Any]] = Field(default=None, description="FieldsV1 holds the first JSON version format as described in the \"FieldsV1\" type.", alias="fieldsV1")
    manager: Optional[StrictStr] = Field(default=None, description="Manager is an identifier of the workflow managing these fields.")
    operation: Optional[StrictStr] = Field(default=None, description="Operation is the type of operation which lead to this ManagedFieldsEntry being created. The only valid values for this field are 'Apply' and 'Update'.")
    subresource: Optional[StrictStr] = Field(default=None, description="Subresource is the name of the subresource used to update that object, or empty string if the object was updated through the main resource. The value of this field is used to distinguish between managers, even if they share the same name. For example, a status update will be distinct from a regular update using the same manager name. Note that the APIVersion field is not related to the Subresource field and it always corresponds to the version of the main resource.")
    time: Optional[datetime] = Field(default=None, description="Time is the timestamp of when the ManagedFields entry was added. The timestamp will also be updated if a field is added, the manager changes any of the owned fields value or removes a field. The timestamp does not update when a field is removed from the entry because another manager took it over.")
    __properties: ClassVar[List[str]] = ["apiVersion", "fieldsType", "fieldsV1", "manager", "operation", "subresource", "time"]

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
        """Create an instance of IoK8sApimachineryPkgApisMetaV1ManagedFieldsEntry from a JSON string"""
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
        """Create an instance of IoK8sApimachineryPkgApisMetaV1ManagedFieldsEntry from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "apiVersion": obj.get("apiVersion"),
            "fieldsType": obj.get("fieldsType"),
            "fieldsV1": obj.get("fieldsV1"),
            "manager": obj.get("manager"),
            "operation": obj.get("operation"),
            "subresource": obj.get("subresource"),
            "time": obj.get("time")
        })
        return _obj

