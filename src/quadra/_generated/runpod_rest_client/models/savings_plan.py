from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SavingsPlan")


@_attrs_define
class SavingsPlan:
    """
    Attributes:
        cost_per_hr (float | Unset):  Example: 0.21.
        end_time (str | Unset):  Example: 2024-07-12T19:14:40.144Z.
        gpu_type_id (str | Unset):  Example: NVIDIA GeForce RTX 4090.
        id (str | Unset):  Example: clkrb4qci0000mb09c7sualzo.
        pod_id (str | Unset):  Example: xedezhzb9la3ye.
        start_time (str | Unset):  Example: 2024-05-12T19:14:40.144Z.
    """

    cost_per_hr: float | Unset = UNSET
    end_time: str | Unset = UNSET
    gpu_type_id: str | Unset = UNSET
    id: str | Unset = UNSET
    pod_id: str | Unset = UNSET
    start_time: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cost_per_hr = self.cost_per_hr

        end_time = self.end_time

        gpu_type_id = self.gpu_type_id

        id = self.id

        pod_id = self.pod_id

        start_time = self.start_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cost_per_hr is not UNSET:
            field_dict["costPerHr"] = cost_per_hr
        if end_time is not UNSET:
            field_dict["endTime"] = end_time
        if gpu_type_id is not UNSET:
            field_dict["gpuTypeId"] = gpu_type_id
        if id is not UNSET:
            field_dict["id"] = id
        if pod_id is not UNSET:
            field_dict["podId"] = pod_id
        if start_time is not UNSET:
            field_dict["startTime"] = start_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cost_per_hr = d.pop("costPerHr", UNSET)

        end_time = d.pop("endTime", UNSET)

        gpu_type_id = d.pop("gpuTypeId", UNSET)

        id = d.pop("id", UNSET)

        pod_id = d.pop("podId", UNSET)

        start_time = d.pop("startTime", UNSET)

        savings_plan = cls(
            cost_per_hr=cost_per_hr,
            end_time=end_time,
            gpu_type_id=gpu_type_id,
            id=id,
            pod_id=pod_id,
            start_time=start_time,
        )

        savings_plan.additional_properties = d
        return savings_plan

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
