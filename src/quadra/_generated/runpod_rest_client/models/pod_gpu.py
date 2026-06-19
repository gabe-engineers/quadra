from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PodGpu")


@_attrs_define
class PodGpu:
    """
    Attributes:
        id (str | Unset):
        count (int | Unset): The number of GPUs attached to a Pod. Example: 1.
        display_name (str | Unset):
        secure_price (float | Unset):
        community_price (float | Unset):
        one_month_price (float | Unset):
        three_month_price (float | Unset):
        six_month_price (float | Unset):
        one_week_price (float | Unset):
        community_spot_price (float | Unset):
        secure_spot_price (float | Unset):
    """

    id: str | Unset = UNSET
    count: int | Unset = UNSET
    display_name: str | Unset = UNSET
    secure_price: float | Unset = UNSET
    community_price: float | Unset = UNSET
    one_month_price: float | Unset = UNSET
    three_month_price: float | Unset = UNSET
    six_month_price: float | Unset = UNSET
    one_week_price: float | Unset = UNSET
    community_spot_price: float | Unset = UNSET
    secure_spot_price: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        count = self.count

        display_name = self.display_name

        secure_price = self.secure_price

        community_price = self.community_price

        one_month_price = self.one_month_price

        three_month_price = self.three_month_price

        six_month_price = self.six_month_price

        one_week_price = self.one_week_price

        community_spot_price = self.community_spot_price

        secure_spot_price = self.secure_spot_price

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if count is not UNSET:
            field_dict["count"] = count
        if display_name is not UNSET:
            field_dict["displayName"] = display_name
        if secure_price is not UNSET:
            field_dict["securePrice"] = secure_price
        if community_price is not UNSET:
            field_dict["communityPrice"] = community_price
        if one_month_price is not UNSET:
            field_dict["oneMonthPrice"] = one_month_price
        if three_month_price is not UNSET:
            field_dict["threeMonthPrice"] = three_month_price
        if six_month_price is not UNSET:
            field_dict["sixMonthPrice"] = six_month_price
        if one_week_price is not UNSET:
            field_dict["oneWeekPrice"] = one_week_price
        if community_spot_price is not UNSET:
            field_dict["communitySpotPrice"] = community_spot_price
        if secure_spot_price is not UNSET:
            field_dict["secureSpotPrice"] = secure_spot_price

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        count = d.pop("count", UNSET)

        display_name = d.pop("displayName", UNSET)

        secure_price = d.pop("securePrice", UNSET)

        community_price = d.pop("communityPrice", UNSET)

        one_month_price = d.pop("oneMonthPrice", UNSET)

        three_month_price = d.pop("threeMonthPrice", UNSET)

        six_month_price = d.pop("sixMonthPrice", UNSET)

        one_week_price = d.pop("oneWeekPrice", UNSET)

        community_spot_price = d.pop("communitySpotPrice", UNSET)

        secure_spot_price = d.pop("secureSpotPrice", UNSET)

        pod_gpu = cls(
            id=id,
            count=count,
            display_name=display_name,
            secure_price=secure_price,
            community_price=community_price,
            one_month_price=one_month_price,
            three_month_price=three_month_price,
            six_month_price=six_month_price,
            one_week_price=one_week_price,
            community_spot_price=community_spot_price,
            secure_spot_price=secure_spot_price,
        )

        pod_gpu.additional_properties = d
        return pod_gpu

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
