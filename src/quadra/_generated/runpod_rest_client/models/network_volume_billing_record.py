from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="NetworkVolumeBillingRecord")


@_attrs_define
class NetworkVolumeBillingRecord:
    """
    Attributes:
        amount (float | Unset): The amount charged for the group for the billing period, in USD. Example: 100.5.
        disk_space_billed_gb (int | Unset): The amount of disk space billed for the billing period, in gigabytes (GB).
            Does not apply to all resource types. Example: 50.
        high_performance_storage_amount (float | Unset): The amount charged for high performance storage for the billing
            period, in USD. Example: 100.5.
        high_performance_storage_disk_space_billed_gb (int | Unset): The amount of high performance storage disk space
            billed for the billing period, in gigabytes (GB). Example: 50.
        time (datetime.datetime | Unset): The start of the period for which the billing record applies. Example:
            2023-01-01T00:00:00Z.
    """

    amount: float | Unset = UNSET
    disk_space_billed_gb: int | Unset = UNSET
    high_performance_storage_amount: float | Unset = UNSET
    high_performance_storage_disk_space_billed_gb: int | Unset = UNSET
    time: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        amount = self.amount

        disk_space_billed_gb = self.disk_space_billed_gb

        high_performance_storage_amount = self.high_performance_storage_amount

        high_performance_storage_disk_space_billed_gb = self.high_performance_storage_disk_space_billed_gb

        time: str | Unset = UNSET
        if not isinstance(self.time, Unset):
            time = self.time.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if amount is not UNSET:
            field_dict["amount"] = amount
        if disk_space_billed_gb is not UNSET:
            field_dict["diskSpaceBilledGb"] = disk_space_billed_gb
        if high_performance_storage_amount is not UNSET:
            field_dict["highPerformanceStorageAmount"] = high_performance_storage_amount
        if high_performance_storage_disk_space_billed_gb is not UNSET:
            field_dict["highPerformanceStorageDiskSpaceBilledGb"] = high_performance_storage_disk_space_billed_gb
        if time is not UNSET:
            field_dict["time"] = time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        amount = d.pop("amount", UNSET)

        disk_space_billed_gb = d.pop("diskSpaceBilledGb", UNSET)

        high_performance_storage_amount = d.pop("highPerformanceStorageAmount", UNSET)

        high_performance_storage_disk_space_billed_gb = d.pop("highPerformanceStorageDiskSpaceBilledGb", UNSET)

        _time = d.pop("time", UNSET)
        time: datetime.datetime | Unset
        if isinstance(_time, Unset):
            time = UNSET
        else:
            time = datetime.datetime.fromisoformat(_time)

        network_volume_billing_record = cls(
            amount=amount,
            disk_space_billed_gb=disk_space_billed_gb,
            high_performance_storage_amount=high_performance_storage_amount,
            high_performance_storage_disk_space_billed_gb=high_performance_storage_disk_space_billed_gb,
            time=time,
        )

        network_volume_billing_record.additional_properties = d
        return network_volume_billing_record

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
