from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ContainerRegistryAuthCreateInput")


@_attrs_define
class ContainerRegistryAuthCreateInput:
    """
    Attributes:
        name (str): A user-defined name for a container registry authentication. The name must be unique. Example: my
            creds.
        password (str): The password for the container registry. Example: my-password.
        username (str): The username for the container registry. Example: my-username.
    """

    name: str
    password: str
    username: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        password = self.password

        username = self.username

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "password": password,
                "username": username,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        password = d.pop("password")

        username = d.pop("username")

        container_registry_auth_create_input = cls(
            name=name,
            password=password,
            username=username,
        )

        container_registry_auth_create_input.additional_properties = d
        return container_registry_auth_create_input

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
