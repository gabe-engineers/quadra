from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.template_create_input_category import TemplateCreateInputCategory
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.template_create_input_env import TemplateCreateInputEnv


T = TypeVar("T", bound="TemplateCreateInput")


@_attrs_define
class TemplateCreateInput:
    """
    Attributes:
        image_name (str): Docker image name.
        name (str): Template name.
        category (TemplateCreateInputCategory | Unset): The compute category of the resource defined by this template.
            Default: TemplateCreateInputCategory.NVIDIA.
        container_disk_in_gb (int | Unset): The amount of disk space in GB to allocate for the container. Default: 50.
        container_registry_auth_id (str | Unset): The unique string representing the container auth object needed for a
            private image.
        docker_entrypoint (list[str] | Unset): If specified, overrides the ENTRYPOINT for the Docker image run on the
            Pods using this template. If [], uses the ENTRYPOINT defined in the DockerFile.
        docker_start_cmd (list[str] | Unset): If specified, overrides the start CMD for the Docker image run on the Pods
            using this template. If [], uses the start CMD defined in the DockerFile.
        env (TemplateCreateInputEnv | Unset):  Example: {'ENV_VAR': 'value'}.
        is_public (bool | Unset): If this is a Pod template, specifies whether the template is visible to other Runpod
            users. Default: False.
        is_serverless (bool | Unset): Whether the template specifies a Serverless worker or a Pod. Default: False.
        ports (list[str] | Unset): A list of ports exposed on the created Pod. Each port is formatted as [port
            number]/[protocol]. Protocol can be either http or tcp. Example: ['8888/http', '22/tcp'].
        readme (str | Unset): README content in markdown format. Default: ''.
        volume_in_gb (int | Unset): The amount of disk space, in gigabytes (GB), to allocate on the Pods deployed with
            this template. Default: 20.
        volume_mount_path (str | Unset): If a volume is attached to a Pod deployed with this template, the absolute path
            where the volume will be mounted in the filesystem. Default: '/workspace'.
    """

    image_name: str
    name: str
    category: TemplateCreateInputCategory | Unset = TemplateCreateInputCategory.NVIDIA
    container_disk_in_gb: int | Unset = 50
    container_registry_auth_id: str | Unset = UNSET
    docker_entrypoint: list[str] | Unset = UNSET
    docker_start_cmd: list[str] | Unset = UNSET
    env: TemplateCreateInputEnv | Unset = UNSET
    is_public: bool | Unset = False
    is_serverless: bool | Unset = False
    ports: list[str] | Unset = UNSET
    readme: str | Unset = ""
    volume_in_gb: int | Unset = 20
    volume_mount_path: str | Unset = "/workspace"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        image_name = self.image_name

        name = self.name

        category: str | Unset = UNSET
        if not isinstance(self.category, Unset):
            category = self.category.value

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

        is_public = self.is_public

        is_serverless = self.is_serverless

        ports: list[str] | Unset = UNSET
        if not isinstance(self.ports, Unset):
            ports = self.ports

        readme = self.readme

        volume_in_gb = self.volume_in_gb

        volume_mount_path = self.volume_mount_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "imageName": image_name,
                "name": name,
            }
        )
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
        if env is not UNSET:
            field_dict["env"] = env
        if is_public is not UNSET:
            field_dict["isPublic"] = is_public
        if is_serverless is not UNSET:
            field_dict["isServerless"] = is_serverless
        if ports is not UNSET:
            field_dict["ports"] = ports
        if readme is not UNSET:
            field_dict["readme"] = readme
        if volume_in_gb is not UNSET:
            field_dict["volumeInGb"] = volume_in_gb
        if volume_mount_path is not UNSET:
            field_dict["volumeMountPath"] = volume_mount_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.template_create_input_env import TemplateCreateInputEnv

        d = dict(src_dict)
        image_name = d.pop("imageName")

        name = d.pop("name")

        _category = d.pop("category", UNSET)
        category: TemplateCreateInputCategory | Unset
        if isinstance(_category, Unset):
            category = UNSET
        else:
            category = TemplateCreateInputCategory(_category)

        container_disk_in_gb = d.pop("containerDiskInGb", UNSET)

        container_registry_auth_id = d.pop("containerRegistryAuthId", UNSET)

        docker_entrypoint = cast(list[str], d.pop("dockerEntrypoint", UNSET))

        docker_start_cmd = cast(list[str], d.pop("dockerStartCmd", UNSET))

        _env = d.pop("env", UNSET)
        env: TemplateCreateInputEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = TemplateCreateInputEnv.from_dict(_env)

        is_public = d.pop("isPublic", UNSET)

        is_serverless = d.pop("isServerless", UNSET)

        ports = cast(list[str], d.pop("ports", UNSET))

        readme = d.pop("readme", UNSET)

        volume_in_gb = d.pop("volumeInGb", UNSET)

        volume_mount_path = d.pop("volumeMountPath", UNSET)

        template_create_input = cls(
            image_name=image_name,
            name=name,
            category=category,
            container_disk_in_gb=container_disk_in_gb,
            container_registry_auth_id=container_registry_auth_id,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            env=env,
            is_public=is_public,
            is_serverless=is_serverless,
            ports=ports,
            readme=readme,
            volume_in_gb=volume_in_gb,
            volume_mount_path=volume_mount_path,
        )

        template_create_input.additional_properties = d
        return template_create_input

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
