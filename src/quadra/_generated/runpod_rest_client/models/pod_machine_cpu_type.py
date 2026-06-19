from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PodMachineCpuType")


@_attrs_define
class PodMachineCpuType:
    """
    Attributes:
        id (str | Unset):
        display_name (str | Unset):
        cores (float | Unset):
        threads_per_core (float | Unset):
        group_id (str | Unset):
    """

    id: str | Unset = UNSET
    display_name: str | Unset = UNSET
    cores: float | Unset = UNSET
    threads_per_core: float | Unset = UNSET
    group_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        display_name = self.display_name

        cores = self.cores

        threads_per_core = self.threads_per_core

        group_id = self.group_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if cores is not UNSET:
            field_dict["cores"] = cores
        if threads_per_core is not UNSET:
            field_dict["threadsPerCore"] = threads_per_core
        if group_id is not UNSET:
            field_dict["groupId"] = group_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        display_name = d.pop("displayName", UNSET)

        cores = d.pop("cores", UNSET)

        threads_per_core = d.pop("threadsPerCore", UNSET)

        group_id = d.pop("groupId", UNSET)

        pod_machine_cpu_type = cls(
            id=id,
            display_name=display_name,
            cores=cores,
            threads_per_core=threads_per_core,
            group_id=group_id,
        )

        pod_machine_cpu_type.additional_properties = d
        return pod_machine_cpu_type

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
