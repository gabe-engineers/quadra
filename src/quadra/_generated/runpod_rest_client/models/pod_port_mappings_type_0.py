from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PodPortMappingsType0")


@_attrs_define
class PodPortMappingsType0:
    """A mapping of internal ports to public ports on a Pod. For example, { "22": 10341 } means that port 22 on the Pod is
    mapped to port 10341 and is publicly accessible at [public ip]:10341. If the Pod is still initializing, this mapping
    is not yet determined and will be empty.

        Example:
            {'22': 10341}

    """

    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pod_port_mappings_type_0 = cls()

        pod_port_mappings_type_0.additional_properties = d
        return pod_port_mappings_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
