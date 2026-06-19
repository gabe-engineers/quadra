from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.pod_create_input_allowed_cuda_versions_item import PodCreateInputAllowedCudaVersionsItem
from ..models.pod_create_input_cloud_type import PodCreateInputCloudType
from ..models.pod_create_input_compute_type import PodCreateInputComputeType
from ..models.pod_create_input_cpu_flavor_ids_item import PodCreateInputCpuFlavorIdsItem
from ..models.pod_create_input_cpu_flavor_priority import PodCreateInputCpuFlavorPriority
from ..models.pod_create_input_data_center_ids_item import PodCreateInputDataCenterIdsItem
from ..models.pod_create_input_data_center_priority import PodCreateInputDataCenterPriority
from ..models.pod_create_input_gpu_type_ids_item import PodCreateInputGpuTypeIdsItem
from ..models.pod_create_input_gpu_type_priority import PodCreateInputGpuTypePriority
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pod_create_input_env import PodCreateInputEnv


T = TypeVar("T", bound="PodCreateInput")


@_attrs_define
class PodCreateInput:
    """
    Attributes:
        allowed_cuda_versions (list[PodCreateInputAllowedCudaVersionsItem] | Unset): If the created Pod is a GPU Pod, a
            list of acceptable CUDA versions on the [Pod](#/components/schemas/Pod). If not set, any CUDA version is
            acceptable.
        cloud_type (PodCreateInputCloudType | Unset): Set to SECURE to create the Pod in Secure Cloud. Set to COMMUNITY
            to create the Pod in Community Cloud. To determine which one suits your needs, see
            https://docs.runpod.io/pods/overview#pod-types. Default: PodCreateInputCloudType.SECURE.
        compute_type (PodCreateInputComputeType | Unset): Set to GPU to create a GPU Pod. Set to CPU to create a CPU
            Pod. If set to CPU, the Pod will not have a GPU attached and properties related to GPUs such as gpuTypeIds will
            be ignored. If set to GPU, the Pod will have a GPU attached and properties related to CPUs such as cpuFlavorIds
            will be ignored. Default: PodCreateInputComputeType.GPU.
        container_disk_in_gb (int | None | Unset): The amount of disk space, in gigabytes (GB), to allocate on the
            container disk for the created Pod. The data on the container disk is wiped when the Pod restarts. To persist
            data across Pod restarts, set volumeInGb to configure the Pod network volume. Default: 50.
        container_registry_auth_id (str | Unset): Registry credentials ID. Example: clzdaifot0001l90809257ynb.
        country_codes (list[str] | Unset): A list of country codes where the created Pod can be located. If not set, the
            Pod can be located in any country.
        cpu_flavor_ids (list[PodCreateInputCpuFlavorIdsItem] | Unset): If the created Pod is a CPU Pod, a list of Runpod
            CPU flavors which can be attached to the Pod. The order of the list determines the order to rent CPU flavors.
            See cpuFlavorPriority for how the order of the list affects Pod creation.
        cpu_flavor_priority (PodCreateInputCpuFlavorPriority | Unset): If the created Pod is a CPU Pod, set to
            availability to respond to current CPU flavor availability. Set to custom to always try to rent CPU flavors in
            the order specified in cpuFlavorIds. Default: PodCreateInputCpuFlavorPriority.AVAILABILITY.
        data_center_ids (list[PodCreateInputDataCenterIdsItem] | Unset): A list of Runpod data center IDs where the
            created Pod can be located. See `dataCenterPriority` for information on how the order of the list affects Pod
            creation. Example: ['EU-RO-1', 'CA-MTL-1'].
        data_center_priority (PodCreateInputDataCenterPriority | Unset): Set to availability to respond to current
            machine availability. Set to custom to always try to rent machines from data centers in the order specified in
            dataCenterIds. Default: PodCreateInputDataCenterPriority.AVAILABILITY.
        docker_entrypoint (list[str] | Unset): If specified, overrides the ENTRYPOINT for the Docker image run on the
            created Pod. If [], uses the ENTRYPOINT defined in the image.
        docker_start_cmd (list[str] | Unset): If specified, overrides the start CMD for the Docker image run on the
            created Pod. If [], uses the start CMD defined in the image.
        env (PodCreateInputEnv | Unset):  Example: {'ENV_VAR': 'value'}.
        global_networking (bool | Unset): Set to true to enable global networking for the created Pod. Currently only
            available for On-Demand GPU Pods on some Secure Cloud data centers. Default: False. Example: True.
        gpu_count (int | Unset): If the created Pod is a GPU Pod, the number of GPUs attached to the created Pod.
            Default: 1.
        gpu_type_ids (list[PodCreateInputGpuTypeIdsItem] | Unset): If the created Pod is a GPU Pod, a list of Runpod GPU
            types which can be attached to the created Pod. The order of the list determines the order to rent GPU types.
            See `gpuTypePriority` for information on how the order of the list affects Pod creation.
        gpu_type_priority (PodCreateInputGpuTypePriority | Unset): If the created Pod is a GPU Pod, set to availability
            to respond to current GPU type availability. Set to custom to always try to rent GPU types in the order
            specified in gpuTypeIds. Default: PodCreateInputGpuTypePriority.AVAILABILITY.
        image_name (str | Unset): The image tag for the container run on the created Pod. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        interruptible (bool | Unset): Set to true to create an interruptible or spot Pod. An interruptible Pod can be
            rented at a lower cost but can be stopped at any time to free up resources for another Pod. A reserved Pod is
            rented at a higher cost but runs until it exits or is manually stopped. Default: False.
        locked (bool | Unset): Set to true to lock a Pod. Locking a Pod disables stopping or resetting the Pod. Default:
            False.
        min_disk_bandwidth_m_bps (float | Unset): The minimum disk bandwidth, in megabytes per second (MBps), for the
            created Pod.
        min_download_mbps (float | Unset): The minimum download speed, in megabits per second (Mbps), for the created
            Pod.
        min_ram_per_gpu (int | Unset): If the created Pod is a GPU Pod, the minimum amount of RAM, in gigabytes (GB),
            allocated to the created Pod for each GPU attached to the Pod. Default: 8.
        min_upload_mbps (float | Unset): The minimum upload speed, in megabits per second (Mbps), for the created Pod.
        min_vcpu_per_gpu (int | Unset): If the created Pod is a GPU Pod, the minimum number of virtual CPUs allocated to
            the created Pod for each GPU attached to the Pod. Default: 2.
        name (str | Unset): A user-defined name for the created Pod. The name does not need to be unique. Default: 'my
            pod'.
        network_volume_id (str | Unset): The unique string identifying the network volume to attach to the created Pod.
            If attached, a network volume replaces the Pod network volume.
        ports (list[str] | Unset): A list of ports exposed on the created Pod. Each port is formatted as [port
            number]/[protocol]. Protocol can be either http or tcp. Example: ['8888/http', '22/tcp'].
        support_public_ip (bool | Unset): If the created Pod is on Community Cloud, set to true if you need the Pod to
            expose a public IP address. If null, the Pod might not have a public IP address. On Secure Cloud, the Pod will
            always have a public IP address. Example: True.
        template_id (str | Unset): If the Pod is created with a template, the unique string identifying that template.
        vcpu_count (int | Unset): If the created Pod is a CPU Pod, the number of vCPUs allocated to the Pod. Default: 2.
        volume_in_gb (int | None | Unset): The amount of disk space, in gigabytes (GB), to allocate on the Pod volume
            for the created Pod. The data on the Pod volume is persisted across Pod restarts. To persist data so that future
            Pods can access it, create a network volume and set networkVolumeId to attach it to the Pod. Default: 20.
        volume_mount_path (str | Unset): If either a Pod volume or a network volume is attached to a Pod, the absolute
            path where the network volume will be mounted in the filesystem. Default: '/workspace'.
    """

    allowed_cuda_versions: list[PodCreateInputAllowedCudaVersionsItem] | Unset = UNSET
    cloud_type: PodCreateInputCloudType | Unset = PodCreateInputCloudType.SECURE
    compute_type: PodCreateInputComputeType | Unset = PodCreateInputComputeType.GPU
    container_disk_in_gb: int | None | Unset = 50
    container_registry_auth_id: str | Unset = UNSET
    country_codes: list[str] | Unset = UNSET
    cpu_flavor_ids: list[PodCreateInputCpuFlavorIdsItem] | Unset = UNSET
    cpu_flavor_priority: PodCreateInputCpuFlavorPriority | Unset = PodCreateInputCpuFlavorPriority.AVAILABILITY
    data_center_ids: list[PodCreateInputDataCenterIdsItem] | Unset = UNSET
    data_center_priority: PodCreateInputDataCenterPriority | Unset = PodCreateInputDataCenterPriority.AVAILABILITY
    docker_entrypoint: list[str] | Unset = UNSET
    docker_start_cmd: list[str] | Unset = UNSET
    env: PodCreateInputEnv | Unset = UNSET
    global_networking: bool | Unset = False
    gpu_count: int | Unset = 1
    gpu_type_ids: list[PodCreateInputGpuTypeIdsItem] | Unset = UNSET
    gpu_type_priority: PodCreateInputGpuTypePriority | Unset = PodCreateInputGpuTypePriority.AVAILABILITY
    image_name: str | Unset = UNSET
    interruptible: bool | Unset = False
    locked: bool | Unset = False
    min_disk_bandwidth_m_bps: float | Unset = UNSET
    min_download_mbps: float | Unset = UNSET
    min_ram_per_gpu: int | Unset = 8
    min_upload_mbps: float | Unset = UNSET
    min_vcpu_per_gpu: int | Unset = 2
    name: str | Unset = "my pod"
    network_volume_id: str | Unset = UNSET
    ports: list[str] | Unset = UNSET
    support_public_ip: bool | Unset = UNSET
    template_id: str | Unset = UNSET
    vcpu_count: int | Unset = 2
    volume_in_gb: int | None | Unset = 20
    volume_mount_path: str | Unset = "/workspace"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allowed_cuda_versions: list[str] | Unset = UNSET
        if not isinstance(self.allowed_cuda_versions, Unset):
            allowed_cuda_versions = []
            for allowed_cuda_versions_item_data in self.allowed_cuda_versions:
                allowed_cuda_versions_item = allowed_cuda_versions_item_data.value
                allowed_cuda_versions.append(allowed_cuda_versions_item)

        cloud_type: str | Unset = UNSET
        if not isinstance(self.cloud_type, Unset):
            cloud_type = self.cloud_type.value

        compute_type: str | Unset = UNSET
        if not isinstance(self.compute_type, Unset):
            compute_type = self.compute_type.value

        container_disk_in_gb: int | None | Unset
        if isinstance(self.container_disk_in_gb, Unset):
            container_disk_in_gb = UNSET
        else:
            container_disk_in_gb = self.container_disk_in_gb

        container_registry_auth_id = self.container_registry_auth_id

        country_codes: list[str] | Unset = UNSET
        if not isinstance(self.country_codes, Unset):
            country_codes = self.country_codes

        cpu_flavor_ids: list[str] | Unset = UNSET
        if not isinstance(self.cpu_flavor_ids, Unset):
            cpu_flavor_ids = []
            for cpu_flavor_ids_item_data in self.cpu_flavor_ids:
                cpu_flavor_ids_item = cpu_flavor_ids_item_data.value
                cpu_flavor_ids.append(cpu_flavor_ids_item)

        cpu_flavor_priority: str | Unset = UNSET
        if not isinstance(self.cpu_flavor_priority, Unset):
            cpu_flavor_priority = self.cpu_flavor_priority.value

        data_center_ids: list[str] | Unset = UNSET
        if not isinstance(self.data_center_ids, Unset):
            data_center_ids = []
            for data_center_ids_item_data in self.data_center_ids:
                data_center_ids_item = data_center_ids_item_data.value
                data_center_ids.append(data_center_ids_item)

        data_center_priority: str | Unset = UNSET
        if not isinstance(self.data_center_priority, Unset):
            data_center_priority = self.data_center_priority.value

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

        gpu_count = self.gpu_count

        gpu_type_ids: list[str] | Unset = UNSET
        if not isinstance(self.gpu_type_ids, Unset):
            gpu_type_ids = []
            for gpu_type_ids_item_data in self.gpu_type_ids:
                gpu_type_ids_item = gpu_type_ids_item_data.value
                gpu_type_ids.append(gpu_type_ids_item)

        gpu_type_priority: str | Unset = UNSET
        if not isinstance(self.gpu_type_priority, Unset):
            gpu_type_priority = self.gpu_type_priority.value

        image_name = self.image_name

        interruptible = self.interruptible

        locked = self.locked

        min_disk_bandwidth_m_bps = self.min_disk_bandwidth_m_bps

        min_download_mbps = self.min_download_mbps

        min_ram_per_gpu = self.min_ram_per_gpu

        min_upload_mbps = self.min_upload_mbps

        min_vcpu_per_gpu = self.min_vcpu_per_gpu

        name = self.name

        network_volume_id = self.network_volume_id

        ports: list[str] | Unset = UNSET
        if not isinstance(self.ports, Unset):
            ports = self.ports

        support_public_ip = self.support_public_ip

        template_id = self.template_id

        vcpu_count = self.vcpu_count

        volume_in_gb: int | None | Unset
        if isinstance(self.volume_in_gb, Unset):
            volume_in_gb = UNSET
        else:
            volume_in_gb = self.volume_in_gb

        volume_mount_path = self.volume_mount_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if allowed_cuda_versions is not UNSET:
            field_dict["allowedCudaVersions"] = allowed_cuda_versions
        if cloud_type is not UNSET:
            field_dict["cloudType"] = cloud_type
        if compute_type is not UNSET:
            field_dict["computeType"] = compute_type
        if container_disk_in_gb is not UNSET:
            field_dict["containerDiskInGb"] = container_disk_in_gb
        if container_registry_auth_id is not UNSET:
            field_dict["containerRegistryAuthId"] = container_registry_auth_id
        if country_codes is not UNSET:
            field_dict["countryCodes"] = country_codes
        if cpu_flavor_ids is not UNSET:
            field_dict["cpuFlavorIds"] = cpu_flavor_ids
        if cpu_flavor_priority is not UNSET:
            field_dict["cpuFlavorPriority"] = cpu_flavor_priority
        if data_center_ids is not UNSET:
            field_dict["dataCenterIds"] = data_center_ids
        if data_center_priority is not UNSET:
            field_dict["dataCenterPriority"] = data_center_priority
        if docker_entrypoint is not UNSET:
            field_dict["dockerEntrypoint"] = docker_entrypoint
        if docker_start_cmd is not UNSET:
            field_dict["dockerStartCmd"] = docker_start_cmd
        if env is not UNSET:
            field_dict["env"] = env
        if global_networking is not UNSET:
            field_dict["globalNetworking"] = global_networking
        if gpu_count is not UNSET:
            field_dict["gpuCount"] = gpu_count
        if gpu_type_ids is not UNSET:
            field_dict["gpuTypeIds"] = gpu_type_ids
        if gpu_type_priority is not UNSET:
            field_dict["gpuTypePriority"] = gpu_type_priority
        if image_name is not UNSET:
            field_dict["imageName"] = image_name
        if interruptible is not UNSET:
            field_dict["interruptible"] = interruptible
        if locked is not UNSET:
            field_dict["locked"] = locked
        if min_disk_bandwidth_m_bps is not UNSET:
            field_dict["minDiskBandwidthMBps"] = min_disk_bandwidth_m_bps
        if min_download_mbps is not UNSET:
            field_dict["minDownloadMbps"] = min_download_mbps
        if min_ram_per_gpu is not UNSET:
            field_dict["minRAMPerGPU"] = min_ram_per_gpu
        if min_upload_mbps is not UNSET:
            field_dict["minUploadMbps"] = min_upload_mbps
        if min_vcpu_per_gpu is not UNSET:
            field_dict["minVCPUPerGPU"] = min_vcpu_per_gpu
        if name is not UNSET:
            field_dict["name"] = name
        if network_volume_id is not UNSET:
            field_dict["networkVolumeId"] = network_volume_id
        if ports is not UNSET:
            field_dict["ports"] = ports
        if support_public_ip is not UNSET:
            field_dict["supportPublicIp"] = support_public_ip
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if vcpu_count is not UNSET:
            field_dict["vcpuCount"] = vcpu_count
        if volume_in_gb is not UNSET:
            field_dict["volumeInGb"] = volume_in_gb
        if volume_mount_path is not UNSET:
            field_dict["volumeMountPath"] = volume_mount_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pod_create_input_env import PodCreateInputEnv

        d = dict(src_dict)
        _allowed_cuda_versions = d.pop("allowedCudaVersions", UNSET)
        allowed_cuda_versions: list[PodCreateInputAllowedCudaVersionsItem] | Unset = UNSET
        if _allowed_cuda_versions is not UNSET:
            allowed_cuda_versions = []
            for allowed_cuda_versions_item_data in _allowed_cuda_versions:
                allowed_cuda_versions_item = PodCreateInputAllowedCudaVersionsItem(allowed_cuda_versions_item_data)

                allowed_cuda_versions.append(allowed_cuda_versions_item)

        _cloud_type = d.pop("cloudType", UNSET)
        cloud_type: PodCreateInputCloudType | Unset
        if isinstance(_cloud_type, Unset):
            cloud_type = UNSET
        else:
            cloud_type = PodCreateInputCloudType(_cloud_type)

        _compute_type = d.pop("computeType", UNSET)
        compute_type: PodCreateInputComputeType | Unset
        if isinstance(_compute_type, Unset):
            compute_type = UNSET
        else:
            compute_type = PodCreateInputComputeType(_compute_type)

        def _parse_container_disk_in_gb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        container_disk_in_gb = _parse_container_disk_in_gb(d.pop("containerDiskInGb", UNSET))

        container_registry_auth_id = d.pop("containerRegistryAuthId", UNSET)

        country_codes = cast(list[str], d.pop("countryCodes", UNSET))

        _cpu_flavor_ids = d.pop("cpuFlavorIds", UNSET)
        cpu_flavor_ids: list[PodCreateInputCpuFlavorIdsItem] | Unset = UNSET
        if _cpu_flavor_ids is not UNSET:
            cpu_flavor_ids = []
            for cpu_flavor_ids_item_data in _cpu_flavor_ids:
                cpu_flavor_ids_item = PodCreateInputCpuFlavorIdsItem(cpu_flavor_ids_item_data)

                cpu_flavor_ids.append(cpu_flavor_ids_item)

        _cpu_flavor_priority = d.pop("cpuFlavorPriority", UNSET)
        cpu_flavor_priority: PodCreateInputCpuFlavorPriority | Unset
        if isinstance(_cpu_flavor_priority, Unset):
            cpu_flavor_priority = UNSET
        else:
            cpu_flavor_priority = PodCreateInputCpuFlavorPriority(_cpu_flavor_priority)

        _data_center_ids = d.pop("dataCenterIds", UNSET)
        data_center_ids: list[PodCreateInputDataCenterIdsItem] | Unset = UNSET
        if _data_center_ids is not UNSET:
            data_center_ids = []
            for data_center_ids_item_data in _data_center_ids:
                data_center_ids_item = PodCreateInputDataCenterIdsItem(data_center_ids_item_data)

                data_center_ids.append(data_center_ids_item)

        _data_center_priority = d.pop("dataCenterPriority", UNSET)
        data_center_priority: PodCreateInputDataCenterPriority | Unset
        if isinstance(_data_center_priority, Unset):
            data_center_priority = UNSET
        else:
            data_center_priority = PodCreateInputDataCenterPriority(_data_center_priority)

        docker_entrypoint = cast(list[str], d.pop("dockerEntrypoint", UNSET))

        docker_start_cmd = cast(list[str], d.pop("dockerStartCmd", UNSET))

        _env = d.pop("env", UNSET)
        env: PodCreateInputEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = PodCreateInputEnv.from_dict(_env)

        global_networking = d.pop("globalNetworking", UNSET)

        gpu_count = d.pop("gpuCount", UNSET)

        _gpu_type_ids = d.pop("gpuTypeIds", UNSET)
        gpu_type_ids: list[PodCreateInputGpuTypeIdsItem] | Unset = UNSET
        if _gpu_type_ids is not UNSET:
            gpu_type_ids = []
            for gpu_type_ids_item_data in _gpu_type_ids:
                gpu_type_ids_item = PodCreateInputGpuTypeIdsItem(gpu_type_ids_item_data)

                gpu_type_ids.append(gpu_type_ids_item)

        _gpu_type_priority = d.pop("gpuTypePriority", UNSET)
        gpu_type_priority: PodCreateInputGpuTypePriority | Unset
        if isinstance(_gpu_type_priority, Unset):
            gpu_type_priority = UNSET
        else:
            gpu_type_priority = PodCreateInputGpuTypePriority(_gpu_type_priority)

        image_name = d.pop("imageName", UNSET)

        interruptible = d.pop("interruptible", UNSET)

        locked = d.pop("locked", UNSET)

        min_disk_bandwidth_m_bps = d.pop("minDiskBandwidthMBps", UNSET)

        min_download_mbps = d.pop("minDownloadMbps", UNSET)

        min_ram_per_gpu = d.pop("minRAMPerGPU", UNSET)

        min_upload_mbps = d.pop("minUploadMbps", UNSET)

        min_vcpu_per_gpu = d.pop("minVCPUPerGPU", UNSET)

        name = d.pop("name", UNSET)

        network_volume_id = d.pop("networkVolumeId", UNSET)

        ports = cast(list[str], d.pop("ports", UNSET))

        support_public_ip = d.pop("supportPublicIp", UNSET)

        template_id = d.pop("templateId", UNSET)

        vcpu_count = d.pop("vcpuCount", UNSET)

        def _parse_volume_in_gb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        volume_in_gb = _parse_volume_in_gb(d.pop("volumeInGb", UNSET))

        volume_mount_path = d.pop("volumeMountPath", UNSET)

        pod_create_input = cls(
            allowed_cuda_versions=allowed_cuda_versions,
            cloud_type=cloud_type,
            compute_type=compute_type,
            container_disk_in_gb=container_disk_in_gb,
            container_registry_auth_id=container_registry_auth_id,
            country_codes=country_codes,
            cpu_flavor_ids=cpu_flavor_ids,
            cpu_flavor_priority=cpu_flavor_priority,
            data_center_ids=data_center_ids,
            data_center_priority=data_center_priority,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            env=env,
            global_networking=global_networking,
            gpu_count=gpu_count,
            gpu_type_ids=gpu_type_ids,
            gpu_type_priority=gpu_type_priority,
            image_name=image_name,
            interruptible=interruptible,
            locked=locked,
            min_disk_bandwidth_m_bps=min_disk_bandwidth_m_bps,
            min_download_mbps=min_download_mbps,
            min_ram_per_gpu=min_ram_per_gpu,
            min_upload_mbps=min_upload_mbps,
            min_vcpu_per_gpu=min_vcpu_per_gpu,
            name=name,
            network_volume_id=network_volume_id,
            ports=ports,
            support_public_ip=support_public_ip,
            template_id=template_id,
            vcpu_count=vcpu_count,
            volume_in_gb=volume_in_gb,
            volume_mount_path=volume_mount_path,
        )

        pod_create_input.additional_properties = d
        return pod_create_input

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
