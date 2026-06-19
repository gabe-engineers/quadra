from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pod_update_input_env import PodUpdateInputEnv


T = TypeVar("T", bound="PodUpdateInput")


@_attrs_define
class PodUpdateInput:
    """Input for updating a Pod which will trigger a reset.

    Attributes:
        container_disk_in_gb (int | None | Unset): The amount of disk space, in gigabytes (GB), to allocate on the
            container disk for the created Pod. The data on the container disk is wiped when the Pod restarts. To persist
            data across Pod restarts, set volumeInGb to configure the Pod network volume. Default: 50.
        container_registry_auth_id (str | Unset): Registry credentials ID. Example: clzdaifot0001l90809257ynb.
        docker_entrypoint (list[str] | Unset): If specified, overrides the ENTRYPOINT for the Docker image run on the
            created Pod. If [], uses the ENTRYPOINT defined in the image.
        docker_start_cmd (list[str] | Unset): If specified, overrides the start CMD for the Docker image run on the
            created Pod. If [], uses the start CMD defined in the image.
        env (PodUpdateInputEnv | Unset):  Example: {'ENV_VAR': 'value'}.
        global_networking (bool | Unset): Set to true to enable global networking for the created Pod. Currently only
            available for On-Demand GPU Pods on some Secure Cloud data centers. Default: False. Example: True.
        image_name (str | Unset): The image tag for the container run on the created Pod. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        locked (bool | Unset): Set to true to lock a Pod. Locking a Pod disables stopping or resetting the Pod. Default:
            False.
        name (str | Unset): A user-defined name for the created Pod. The name does not need to be unique. Default: 'my
            pod'.
        ports (list[str] | Unset): A list of ports exposed on the created Pod. Each port is formatted as [port
            number]/[protocol]. Protocol can be either http or tcp. Example: ['8888/http', '22/tcp'].
        volume_in_gb (int | None | Unset): The amount of disk space, in gigabytes (GB), to allocate on the Pod volume
            for the created Pod. The data on the Pod volume is persisted across Pod restarts. To persist data so that future
            Pods can access it, create a network volume and set networkVolumeId to attach it to the Pod. Default: 20.
        volume_mount_path (str | Unset): If either a Pod volume or a network volume is attached to a Pod, the absolute
            path where the network volume will be mounted in the filesystem. Default: '/workspace'.
    """

    container_disk_in_gb: int | None | Unset = 50
    container_registry_auth_id: str | Unset = UNSET
    docker_entrypoint: list[str] | Unset = UNSET
    docker_start_cmd: list[str] | Unset = UNSET
    env: PodUpdateInputEnv | Unset = UNSET
    global_networking: bool | Unset = False
    image_name: str | Unset = UNSET
    locked: bool | Unset = False
    name: str | Unset = "my pod"
    ports: list[str] | Unset = UNSET
    volume_in_gb: int | None | Unset = 20
    volume_mount_path: str | Unset = "/workspace"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        container_disk_in_gb: int | None | Unset
        if isinstance(self.container_disk_in_gb, Unset):
            container_disk_in_gb = UNSET
        else:
            container_disk_in_gb = self.container_disk_in_gb

        container_registry_auth_id = self.container_registry_auth_id

        docker_entrypoint: list[str] | Unset = UNSET
        if not isinstance(self.docker_entrypoint, Unset):
            docker_entrypoint = self.docker_entrypoint

        docker_start_cmd: list[str] | Unset = UNSET
        if not isinstance(self.docker_start_cmd, Unset):
            docker_start_cmd = self.docker_start_cmd

        env: dict[str, Any] | Unset = UNSET
        if not isinstance(self.env, Unset):
            env = self.env.to_dict()

        global_networking = self.global_networking

        image_name = self.image_name

        locked = self.locked

        name = self.name

        ports: list[str] | Unset = UNSET
        if not isinstance(self.ports, Unset):
            ports = self.ports

        volume_in_gb: int | None | Unset
        if isinstance(self.volume_in_gb, Unset):
            volume_in_gb = UNSET
        else:
            volume_in_gb = self.volume_in_gb

        volume_mount_path = self.volume_mount_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if container_disk_in_gb is not UNSET:
            field_dict["containerDiskInGb"] = container_disk_in_gb
        if container_registry_auth_id is not UNSET:
            field_dict["containerRegistryAuthId"] = container_registry_auth_id
        if docker_entrypoint is not UNSET:
            field_dict["dockerEntrypoint"] = docker_entrypoint
        if docker_start_cmd is not UNSET:
            field_dict["dockerStartCmd"] = docker_start_cmd
        if env is not UNSET:
            field_dict["env"] = env
        if global_networking is not UNSET:
            field_dict["globalNetworking"] = global_networking
        if image_name is not UNSET:
            field_dict["imageName"] = image_name
        if locked is not UNSET:
            field_dict["locked"] = locked
        if name is not UNSET:
            field_dict["name"] = name
        if ports is not UNSET:
            field_dict["ports"] = ports
        if volume_in_gb is not UNSET:
            field_dict["volumeInGb"] = volume_in_gb
        if volume_mount_path is not UNSET:
            field_dict["volumeMountPath"] = volume_mount_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pod_update_input_env import PodUpdateInputEnv

        d = dict(src_dict)

        def _parse_container_disk_in_gb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        container_disk_in_gb = _parse_container_disk_in_gb(d.pop("containerDiskInGb", UNSET))

        container_registry_auth_id = d.pop("containerRegistryAuthId", UNSET)

        docker_entrypoint = cast(list[str], d.pop("dockerEntrypoint", UNSET))

        docker_start_cmd = cast(list[str], d.pop("dockerStartCmd", UNSET))

        _env = d.pop("env", UNSET)
        env: PodUpdateInputEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = PodUpdateInputEnv.from_dict(_env)

        global_networking = d.pop("globalNetworking", UNSET)

        image_name = d.pop("imageName", UNSET)

        locked = d.pop("locked", UNSET)

        name = d.pop("name", UNSET)

        ports = cast(list[str], d.pop("ports", UNSET))

        def _parse_volume_in_gb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        volume_in_gb = _parse_volume_in_gb(d.pop("volumeInGb", UNSET))

        volume_mount_path = d.pop("volumeMountPath", UNSET)

        pod_update_input = cls(
            container_disk_in_gb=container_disk_in_gb,
            container_registry_auth_id=container_registry_auth_id,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            env=env,
            global_networking=global_networking,
            image_name=image_name,
            locked=locked,
            name=name,
            ports=ports,
            volume_in_gb=volume_in_gb,
            volume_mount_path=volume_mount_path,
        )

        pod_update_input.additional_properties = d
        return pod_update_input

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
