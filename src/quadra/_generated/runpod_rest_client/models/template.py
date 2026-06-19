from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.template_env import TemplateEnv


T = TypeVar("T", bound="Template")


@_attrs_define
class Template:
    """
    Attributes:
        category (str | Unset): The category of the template. The category can be used to filter templates in the Runpod
            UI. Current categories are NVIDIA, AMD, and CPU. Example: NVIDIA.
        container_disk_in_gb (int | Unset): The amount of disk space, in gigabytes (GB), to allocate on the container
            disk for a Pod or worker. The data on the container disk is wiped when the Pod or worker restarts. To persist
            data across restarts, set volumeInGb to configure the local network volume. Example: 50.
        container_registry_auth_id (str | Unset):
        docker_entrypoint (list[str] | Unset): If specified, overrides the ENTRYPOINT for the Docker image run on a Pod
            or worker. If [], uses the ENTRYPOINT defined in the image.
        docker_start_cmd (list[str] | Unset): If specified, overrides the start CMD for the Docker image run on a Pod or
            worker. If [], uses the start CMD defined in the image.
        earned (float | Unset): The amount of Runpod credits earned by the creator of a template by all Pods or workers
            created from the template. Example: 100.
        env (TemplateEnv | Unset):  Example: {'ENV_VAR': 'value'}.
        id (str | Unset): A unique string identifying a template. Example: 30zmvf89kd.
        image_name (str | Unset): The image tag for the container run on Pods or workers created from a template.
            Example: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        is_public (bool | Unset): Set to true if a template is public and can be used by any Runpod user. Set to false
            if a template is private and can only be used by the creator.
        is_runpod (bool | Unset): If true, a template is an official template managed by Runpod. Example: True.
        is_serverless (bool | Unset): If true, instances created from a template are Serverless workers. If false,
            instances created from a template are Pods. Example: True.
        name (str | Unset): A user-defined name for a template. The name needs to be unique. Example: my template.
        ports (list[str] | Unset): A list of ports exposed on a Pod or worker. Each port is formatted as [port
            number]/[protocol]. Protocol can be either http or tcp. Example: ['8888/http', '22/tcp'].
        readme (str | Unset): A string of markdown-formatted text that describes a template. The readme is displayed in
            the Runpod UI when a user selects the template.
        runtime_in_min (int | Unset):
        volume_in_gb (int | Unset): The amount of disk space, in gigabytes (GB), to allocate on the local network volume
            for a Pod or worker. The data on the local network volume is persisted across restarts. To persist data so that
            future Pods and workers can access it, create a network volume and set networkVolumeId to attach it to the Pod
            or worker. Example: 20.
        volume_mount_path (str | Unset): If a local network volume or network volume is attached to a Pod or worker, the
            absolute path where the network volume is mounted in the filesystem. Example: /workspace.
    """

    category: str | Unset = UNSET
    container_disk_in_gb: int | Unset = UNSET
    container_registry_auth_id: str | Unset = UNSET
    docker_entrypoint: list[str] | Unset = UNSET
    docker_start_cmd: list[str] | Unset = UNSET
    earned: float | Unset = UNSET
    env: TemplateEnv | Unset = UNSET
    id: str | Unset = UNSET
    image_name: str | Unset = UNSET
    is_public: bool | Unset = UNSET
    is_runpod: bool | Unset = UNSET
    is_serverless: bool | Unset = UNSET
    name: str | Unset = UNSET
    ports: list[str] | Unset = UNSET
    readme: str | Unset = UNSET
    runtime_in_min: int | Unset = UNSET
    volume_in_gb: int | Unset = UNSET
    volume_mount_path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        category = self.category

        container_disk_in_gb = self.container_disk_in_gb

        container_registry_auth_id = self.container_registry_auth_id

        docker_entrypoint: list[str] | Unset = UNSET
        if not isinstance(self.docker_entrypoint, Unset):
            docker_entrypoint = self.docker_entrypoint

        docker_start_cmd: list[str] | Unset = UNSET
        if not isinstance(self.docker_start_cmd, Unset):
            docker_start_cmd = self.docker_start_cmd

        earned = self.earned

        env: dict[str, Any] | Unset = UNSET
        if not isinstance(self.env, Unset):
            env = self.env.to_dict()

        id = self.id

        image_name = self.image_name

        is_public = self.is_public

        is_runpod = self.is_runpod

        is_serverless = self.is_serverless

        name = self.name

        ports: list[str] | Unset = UNSET
        if not isinstance(self.ports, Unset):
            ports = self.ports

        readme = self.readme

        runtime_in_min = self.runtime_in_min

        volume_in_gb = self.volume_in_gb

        volume_mount_path = self.volume_mount_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if category is not UNSET:
            field_dict["category"] = category
        if container_disk_in_gb is not UNSET:
            field_dict["containerDiskInGb"] = container_disk_in_gb
        if container_registry_auth_id is not UNSET:
            field_dict["containerRegistryAuthId"] = container_registry_auth_id
        if docker_entrypoint is not UNSET:
            field_dict["dockerEntrypoint"] = docker_entrypoint
        if docker_start_cmd is not UNSET:
            field_dict["dockerStartCmd"] = docker_start_cmd
        if earned is not UNSET:
            field_dict["earned"] = earned
        if env is not UNSET:
            field_dict["env"] = env
        if id is not UNSET:
            field_dict["id"] = id
        if image_name is not UNSET:
            field_dict["imageName"] = image_name
        if is_public is not UNSET:
            field_dict["isPublic"] = is_public
        if is_runpod is not UNSET:
            field_dict["isRunpod"] = is_runpod
        if is_serverless is not UNSET:
            field_dict["isServerless"] = is_serverless
        if name is not UNSET:
            field_dict["name"] = name
        if ports is not UNSET:
            field_dict["ports"] = ports
        if readme is not UNSET:
            field_dict["readme"] = readme
        if runtime_in_min is not UNSET:
            field_dict["runtimeInMin"] = runtime_in_min
        if volume_in_gb is not UNSET:
            field_dict["volumeInGb"] = volume_in_gb
        if volume_mount_path is not UNSET:
            field_dict["volumeMountPath"] = volume_mount_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template_env import TemplateEnv

        d = dict(src_dict)
        category = d.pop("category", UNSET)

        container_disk_in_gb = d.pop("containerDiskInGb", UNSET)

        container_registry_auth_id = d.pop("containerRegistryAuthId", UNSET)

        docker_entrypoint = cast(list[str], d.pop("dockerEntrypoint", UNSET))

        docker_start_cmd = cast(list[str], d.pop("dockerStartCmd", UNSET))

        earned = d.pop("earned", UNSET)

        _env = d.pop("env", UNSET)
        env: TemplateEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = TemplateEnv.from_dict(_env)

        id = d.pop("id", UNSET)

        image_name = d.pop("imageName", UNSET)

        is_public = d.pop("isPublic", UNSET)

        is_runpod = d.pop("isRunpod", UNSET)

        is_serverless = d.pop("isServerless", UNSET)

        name = d.pop("name", UNSET)

        ports = cast(list[str], d.pop("ports", UNSET))

        readme = d.pop("readme", UNSET)

        runtime_in_min = d.pop("runtimeInMin", UNSET)

        volume_in_gb = d.pop("volumeInGb", UNSET)

        volume_mount_path = d.pop("volumeMountPath", UNSET)

        template = cls(
            category=category,
            container_disk_in_gb=container_disk_in_gb,
            container_registry_auth_id=container_registry_auth_id,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            earned=earned,
            env=env,
            id=id,
            image_name=image_name,
            is_public=is_public,
            is_runpod=is_runpod,
            is_serverless=is_serverless,
            name=name,
            ports=ports,
            readme=readme,
            runtime_in_min=runtime_in_min,
            volume_in_gb=volume_in_gb,
            volume_mount_path=volume_mount_path,
        )

        template.additional_properties = d
        return template

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
