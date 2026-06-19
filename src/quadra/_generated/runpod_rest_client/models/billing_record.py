from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="BillingRecord")


@_attrs_define
class BillingRecord:
    """
    Attributes:
        amount (float | Unset): The amount charged for the group for the billing period, in USD. Example: 100.5.
        disk_space_billed_gb (int | Unset): The amount of disk space billed for the billing period, in gigabytes (GB).
            Does not apply to all resource types. Example: 50.
        endpoint_id (str | Unset): If grouping by endpoint ID, the endpoint ID of the group.
        gpu_type_id (str | Unset): If grouping by GPU type ID, the GPU type ID of the group.
        pod_id (str | Unset): If grouping by Pod ID, the Pod ID of the group.
        time (datetime.datetime | Unset): The start of the period for which the billing record applies. Example:
            2023-01-01T00:00:00Z.
        time_billed_ms (int | Unset): The total time billed for the billing period, in milliseconds. Does not apply to
            all resource types. Example: 3600000.
    """

    amount: float | Unset = UNSET
    disk_space_billed_gb: int | Unset = UNSET
    endpoint_id: str | Unset = UNSET
    gpu_type_id: str | Unset = UNSET
    pod_id: str | Unset = UNSET
    time: datetime.datetime | Unset = UNSET
    time_billed_ms: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        amount = self.amount

        disk_space_billed_gb = self.disk_space_billed_gb

        endpoint_id = self.endpoint_id

        gpu_type_id = self.gpu_type_id

        pod_id = self.pod_id

        time: str | Unset = UNSET
        if not isinstance(self.time, Unset):
            time = self.time.isoformat()

        time_billed_ms = self.time_billed_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if amount is not UNSET:
            field_dict["amount"] = amount
        if disk_space_billed_gb is not UNSET:
            field_dict["diskSpaceBilledGb"] = disk_space_billed_gb
        if endpoint_id is not UNSET:
            field_dict["endpointId"] = endpoint_id
        if gpu_type_id is not UNSET:
            field_dict["gpuTypeId"] = gpu_type_id
        if pod_id is not UNSET:
            field_dict["podId"] = pod_id
        if time is not UNSET:
            field_dict["time"] = time
        if time_billed_ms is not UNSET:
            field_dict["timeBilledMs"] = time_billed_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        amount = d.pop("amount", UNSET)

        disk_space_billed_gb = d.pop("diskSpaceBilledGb", UNSET)

        endpoint_id = d.pop("endpointId", UNSET)

        gpu_type_id = d.pop("gpuTypeId", UNSET)

        pod_id = d.pop("podId", UNSET)

        _time = d.pop("time", UNSET)
        time: datetime.datetime | Unset
        if isinstance(_time, Unset):
            time = UNSET
        else:
            time = datetime.datetime.fromisoformat(_time)

        time_billed_ms = d.pop("timeBilledMs", UNSET)

        billing_record = cls(
            amount=amount,
            disk_space_billed_gb=disk_space_billed_gb,
            endpoint_id=endpoint_id,
            gpu_type_id=gpu_type_id,
            pod_id=pod_id,
            time=time,
            time_billed_ms=time_billed_ms,
        )

        billing_record.additional_properties = d
        return billing_record

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
