from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TemplateUpdateInPlaceInput")


@_attrs_define
class TemplateUpdateInPlaceInput:
    """
    Attributes:
        is_public (bool | Unset): If this is a Pod template, specifies whether the template is visible to other Runpod
            users. Default: False.
        name (str | Unset): Template name.
        readme (str | Unset): README content in markdown format. Default: ''.
        volume_in_gb (int | Unset): The amount of disk space, in gigabytes (GB), to allocate on the Pods deployed with
            this template. Default: 20.
        volume_mount_path (str | Unset): If a volume is attached to a Pod deployed with this template, the absolute path
            where the volume will be mounted in the filesystem. Default: '/workspace'.
    """

    is_public: bool | Unset = False
    name: str | Unset = UNSET
    readme: str | Unset = ""
    volume_in_gb: int | Unset = 20
    volume_mount_path: str | Unset = "/workspace"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        is_public = self.is_public

        name = self.name

        readme = self.readme

        volume_in_gb = self.volume_in_gb

        volume_mount_path = self.volume_mount_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_public is not UNSET:
            field_dict["isPublic"] = is_public
        if name is not UNSET:
            field_dict["name"] = name
        if readme is not UNSET:
            field_dict["readme"] = readme
        if volume_in_gb is not UNSET:
            field_dict["volumeInGb"] = volume_in_gb
        if volume_mount_path is not UNSET:
            field_dict["volumeMountPath"] = volume_mount_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        is_public = d.pop("isPublic", UNSET)

        name = d.pop("name", UNSET)

        readme = d.pop("readme", UNSET)

        volume_in_gb = d.pop("volumeInGb", UNSET)

        volume_mount_path = d.pop("volumeMountPath", UNSET)

        template_update_in_place_input = cls(
            is_public=is_public,
            name=name,
            readme=readme,
            volume_in_gb=volume_in_gb,
            volume_mount_path=volume_mount_path,
        )

        template_update_in_place_input.additional_properties = d
        return template_update_in_place_input

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
