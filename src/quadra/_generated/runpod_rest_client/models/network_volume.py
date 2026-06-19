from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NetworkVolume")


@_attrs_define
class NetworkVolume:
    """
    Attributes:
        data_center_id (str | Unset): The Runpod data center ID where a network volume is located. Example: EU-RO-1.
        id (str | Unset): A unique string identifying a network volume. Example: agv6w2qcg7.
        name (str | Unset): A user-defined name for a network volume. The name does not need to be unique. Example: my
            network volume.
        size (int | Unset): The amount of disk space, in gigabytes (GB), allocated to a network volume. Example: 50.
    """

    data_center_id: str | Unset = UNSET
    id: str | Unset = UNSET
    name: str | Unset = UNSET
    size: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data_center_id = self.data_center_id

        id = self.id

        name = self.name

        size = self.size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data_center_id is not UNSET:
            field_dict["dataCenterId"] = data_center_id
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if size is not UNSET:
            field_dict["size"] = size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        data_center_id = d.pop("dataCenterId", UNSET)

        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        size = d.pop("size", UNSET)

        network_volume = cls(
            data_center_id=data_center_id,
            id=id,
            name=name,
            size=size,
        )

        network_volume.additional_properties = d
        return network_volume

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
