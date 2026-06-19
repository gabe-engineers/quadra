from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.pod_desired_status import PodDesiredStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pod_env import PodEnv
    from ..models.pod_gpu import PodGpu
    from ..models.pod_machine import PodMachine
    from ..models.pod_network_volume import PodNetworkVolume
    from ..models.pod_port_mappings_type_0 import PodPortMappingsType0
    from ..models.savings_plan import SavingsPlan


T = TypeVar("T", bound="Pod")


@_attrs_define
class Pod:
    """
    Attributes:
        adjusted_cost_per_hr (float | Unset): The effective cost in Runpod credits per hour of running a Pod, adjusted
            by active Savings Plans. Example: 0.69.
        ai_api_id (str | Unset): Synonym for endpointId (legacy name).
        consumer_user_id (str | Unset): A unique string identifying the Runpod user who rents a Pod. Example:
            user_2PyTJrLzeuwfZilRZ7JhCQDuSqo.
        container_disk_in_gb (int | Unset): The amount of disk space, in gigabytes (GB), to allocate on the container
            disk for a Pod. The data on the container disk is wiped when the Pod restarts. To persist data across Pod
            restarts, set volumeInGb to configure the Pod network volume. Example: 50.
        container_registry_auth_id (str | Unset): If a Pod is created with a container registry auth, the unique string
            identifying that container registry auth. Example: clzdaifot0001l90809257ynb.
        cost_per_hr (float | Unset): The cost in Runpod credits per hour of running a Pod. Note that the actual cost may
            be lower if Savings Plans are applied. Example: 0.74.
        cpu_flavor_id (str | Unset): If the Pod is a CPU Pod, the unique string identifying the CPU flavor the Pod is
            running on. Example: cpu3c.
        desired_status (PodDesiredStatus | Unset): The current expected status of a Pod.
        docker_entrypoint (list[str] | Unset): If specified, overrides the ENTRYPOINT for the Docker image run on the
            created Pod. If [], uses the ENTRYPOINT defined in the image.
        docker_start_cmd (list[str] | Unset): If specified, overrides the start CMD for the Docker image run on the
            created Pod. If [], uses the start CMD defined in the image.
        endpoint_id (str | Unset): If the Pod is a Serverless worker, a unique string identifying the associated
            endpoint.
        env (PodEnv | Unset):  Example: {'ENV_VAR': 'value'}.
        gpu (PodGpu | Unset):
        id (str | Unset): A unique string identifying a [Pod](#/components/schema/Pod). Example: xedezhzb9la3ye.
        image (str | Unset): The image tag for the container run on a Pod. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        interruptible (bool | Unset): Describes how a Pod is rented. An interruptible Pod can be rented at a lower cost
            but can be stopped at any time to free up resources for another Pod. A reserved Pod is rented at a higher cost
            but runs until it exits or is manually stopped.
        last_started_at (str | Unset): The UTC timestamp when a Pod was last started. Example: 2024-07-12T19:14:40.144Z.
        last_status_change (str | Unset): A string describing the last lifecycle event on a Pod. Example: Rented by
            User: Fri Jul 12 2024 15:14:40 GMT-0400 (Eastern Daylight Time).
        locked (bool | Unset): Set to true to lock a Pod. Locking a Pod disables stopping or resetting the Pod.
        machine (PodMachine | Unset): Information about the machine a Pod is running on (see
            [Machine](#/components/schemas/Machine)).
        machine_id (str | Unset): A unique string identifying the host machine a Pod is running on. Example:
            s194cr8pls2z.
        memory_in_gb (float | Unset): The amount of RAM, in gigabytes (GB), attached to a Pod. Example: 62.
        name (str | Unset): A user-defined name for the created Pod. The name does not need to be unique.
        network_volume (PodNetworkVolume | Unset): If a network volume is attached to a Pod, information about the
            network volume (see [network volume schema](#/components/schemas/NetworkVolume)).
        port_mappings (None | PodPortMappingsType0 | Unset): A mapping of internal ports to public ports on a Pod. For
            example, { "22": 10341 } means that port 22 on the Pod is mapped to port 10341 and is publicly accessible at
            [public ip]:10341. If the Pod is still initializing, this mapping is not yet determined and will be empty.
            Example: {'22': 10341}.
        ports (list[str] | Unset): A list of ports exposed on a Pod. Each port is formatted as [port number]/[protocol].
            Protocol can be either http or tcp. Example: ['8888/http', '22/tcp'].
        public_ip (None | str | Unset): The public IP address of a Pod. If the Pod is still initializing, this IP is not
            yet determined and will be empty. Example: 100.65.0.119.
        savings_plans (list[SavingsPlan] | Unset): The list of active Savings Plans applied to a Pod (see [Savings
            Plans](#/components/schemas/SavingsPlan)). If none are applied, the list is empty.
        sls_version (int | Unset): If the Pod is a Serverless worker, the version of the associated endpoint (see
            [Endpoint Version](#/components/schemas/Endpoint/version)).
        template_id (str | Unset): If a Pod is created with a template, the unique string identifying that template.
        vcpu_count (float | Unset): The number of virtual CPUs attached to a Pod. Example: 24.
        volume_encrypted (bool | Unset): Set to true if the local network volume of a Pod is encrypted. Can only be set
            when creating a Pod.
        volume_in_gb (int | Unset): The amount of disk space, in gigabytes (GB), to allocate on the Pod volume for a
            Pod. The data on the Pod volume is persisted across Pod restarts. To persist data so that future Pods can access
            it, create a network volume and set networkVolumeId to attach it to the Pod. Example: 20.
        volume_mount_path (str | Unset): If either a Pod volume or a network volume is attached to a Pod, the absolute
            path where the network volume is mounted in the filesystem. Example: /workspace.
    """

    adjusted_cost_per_hr: float | Unset = UNSET
    ai_api_id: str | Unset = UNSET
    consumer_user_id: str | Unset = UNSET
    container_disk_in_gb: int | Unset = UNSET
    container_registry_auth_id: str | Unset = UNSET
    cost_per_hr: float | Unset = UNSET
    cpu_flavor_id: str | Unset = UNSET
    desired_status: PodDesiredStatus | Unset = UNSET
    docker_entrypoint: list[str] | Unset = UNSET
    docker_start_cmd: list[str] | Unset = UNSET
    endpoint_id: str | Unset = UNSET
    env: PodEnv | Unset = UNSET
    gpu: PodGpu | Unset = UNSET
    id: str | Unset = UNSET
    image: str | Unset = UNSET
    interruptible: bool | Unset = UNSET
    last_started_at: str | Unset = UNSET
    last_status_change: str | Unset = UNSET
    locked: bool | Unset = UNSET
    machine: PodMachine | Unset = UNSET
    machine_id: str | Unset = UNSET
    memory_in_gb: float | Unset = UNSET
    name: str | Unset = UNSET
    network_volume: PodNetworkVolume | Unset = UNSET
    port_mappings: None | PodPortMappingsType0 | Unset = UNSET
    ports: list[str] | Unset = UNSET
    public_ip: None | str | Unset = UNSET
    savings_plans: list[SavingsPlan] | Unset = UNSET
    sls_version: int | Unset = UNSET
    template_id: str | Unset = UNSET
    vcpu_count: float | Unset = UNSET
    volume_encrypted: bool | Unset = UNSET
    volume_in_gb: int | Unset = UNSET
    volume_mount_path: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pod_port_mappings_type_0 import PodPortMappingsType0

        adjusted_cost_per_hr = self.adjusted_cost_per_hr

        ai_api_id = self.ai_api_id

        consumer_user_id = self.consumer_user_id

        container_disk_in_gb = self.container_disk_in_gb

        container_registry_auth_id = self.container_registry_auth_id

        cost_per_hr = self.cost_per_hr

        cpu_flavor_id = self.cpu_flavor_id

        desired_status: str | Unset = UNSET
        if not isinstance(self.desired_status, Unset):
            desired_status = self.desired_status.value

        docker_entrypoint: list[str] | Unset = UNSET
        if not isinstance(self.docker_entrypoint, Unset):
            docker_entrypoint = self.docker_entrypoint

        docker_start_cmd: list[str] | Unset = UNSET
        if not isinstance(self.docker_start_cmd, Unset):
            docker_start_cmd = self.docker_start_cmd

        endpoint_id = self.endpoint_id

        env: dict[str, Any] | Unset = UNSET
        if not isinstance(self.env, Unset):
            env = self.env.to_dict()

        gpu: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gpu, Unset):
            gpu = self.gpu.to_dict()

        id = self.id

        image = self.image

        interruptible = self.interruptible

        last_started_at = self.last_started_at

        last_status_change = self.last_status_change

        locked = self.locked

        machine: dict[str, Any] | Unset = UNSET
        if not isinstance(self.machine, Unset):
            machine = self.machine.to_dict()

        machine_id = self.machine_id

        memory_in_gb = self.memory_in_gb

        name = self.name

        network_volume: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_volume, Unset):
            network_volume = self.network_volume.to_dict()

        port_mappings: dict[str, Any] | None | Unset
        if isinstance(self.port_mappings, Unset):
            port_mappings = UNSET
        elif isinstance(self.port_mappings, PodPortMappingsType0):
            port_mappings = self.port_mappings.to_dict()
        else:
            port_mappings = self.port_mappings

        ports: list[str] | Unset = UNSET
        if not isinstance(self.ports, Unset):
            ports = self.ports

        public_ip: None | str | Unset
        if isinstance(self.public_ip, Unset):
            public_ip = UNSET
        else:
            public_ip = self.public_ip

        savings_plans: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.savings_plans, Unset):
            savings_plans = []
            for savings_plans_item_data in self.savings_plans:
                savings_plans_item = savings_plans_item_data.to_dict()
                savings_plans.append(savings_plans_item)

        sls_version = self.sls_version

        template_id = self.template_id

        vcpu_count = self.vcpu_count

        volume_encrypted = self.volume_encrypted

        volume_in_gb = self.volume_in_gb

        volume_mount_path = self.volume_mount_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if adjusted_cost_per_hr is not UNSET:
            field_dict["adjustedCostPerHr"] = adjusted_cost_per_hr
        if ai_api_id is not UNSET:
            field_dict["aiApiId"] = ai_api_id
        if consumer_user_id is not UNSET:
            field_dict["consumerUserId"] = consumer_user_id
        if container_disk_in_gb is not UNSET:
            field_dict["containerDiskInGb"] = container_disk_in_gb
        if container_registry_auth_id is not UNSET:
            field_dict["containerRegistryAuthId"] = container_registry_auth_id
        if cost_per_hr is not UNSET:
            field_dict["costPerHr"] = cost_per_hr
        if cpu_flavor_id is not UNSET:
            field_dict["cpuFlavorId"] = cpu_flavor_id
        if desired_status is not UNSET:
            field_dict["desiredStatus"] = desired_status
        if docker_entrypoint is not UNSET:
            field_dict["dockerEntrypoint"] = docker_entrypoint
        if docker_start_cmd is not UNSET:
            field_dict["dockerStartCmd"] = docker_start_cmd
        if endpoint_id is not UNSET:
            field_dict["endpointId"] = endpoint_id
        if env is not UNSET:
            field_dict["env"] = env
        if gpu is not UNSET:
            field_dict["gpu"] = gpu
        if id is not UNSET:
            field_dict["id"] = id
        if image is not UNSET:
            field_dict["image"] = image
        if interruptible is not UNSET:
            field_dict["interruptible"] = interruptible
        if last_started_at is not UNSET:
            field_dict["lastStartedAt"] = last_started_at
        if last_status_change is not UNSET:
            field_dict["lastStatusChange"] = last_status_change
        if locked is not UNSET:
            field_dict["locked"] = locked
        if machine is not UNSET:
            field_dict["machine"] = machine
        if machine_id is not UNSET:
            field_dict["machineId"] = machine_id
        if memory_in_gb is not UNSET:
            field_dict["memoryInGb"] = memory_in_gb
        if name is not UNSET:
            field_dict["name"] = name
        if network_volume is not UNSET:
            field_dict["networkVolume"] = network_volume
        if port_mappings is not UNSET:
            field_dict["portMappings"] = port_mappings
        if ports is not UNSET:
            field_dict["ports"] = ports
        if public_ip is not UNSET:
            field_dict["publicIp"] = public_ip
        if savings_plans is not UNSET:
            field_dict["savingsPlans"] = savings_plans
        if sls_version is not UNSET:
            field_dict["slsVersion"] = sls_version
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if vcpu_count is not UNSET:
            field_dict["vcpuCount"] = vcpu_count
        if volume_encrypted is not UNSET:
            field_dict["volumeEncrypted"] = volume_encrypted
        if volume_in_gb is not UNSET:
            field_dict["volumeInGb"] = volume_in_gb
        if volume_mount_path is not UNSET:
            field_dict["volumeMountPath"] = volume_mount_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pod_env import PodEnv
        from ..models.pod_gpu import PodGpu
        from ..models.pod_machine import PodMachine
        from ..models.pod_network_volume import PodNetworkVolume
        from ..models.pod_port_mappings_type_0 import PodPortMappingsType0
        from ..models.savings_plan import SavingsPlan

        d = dict(src_dict)
        adjusted_cost_per_hr = d.pop("adjustedCostPerHr", UNSET)

        ai_api_id = d.pop("aiApiId", UNSET)

        consumer_user_id = d.pop("consumerUserId", UNSET)

        container_disk_in_gb = d.pop("containerDiskInGb", UNSET)

        container_registry_auth_id = d.pop("containerRegistryAuthId", UNSET)

        cost_per_hr = d.pop("costPerHr", UNSET)

        cpu_flavor_id = d.pop("cpuFlavorId", UNSET)

        _desired_status = d.pop("desiredStatus", UNSET)
        desired_status: PodDesiredStatus | Unset
        if isinstance(_desired_status, Unset):
            desired_status = UNSET
        else:
            desired_status = PodDesiredStatus(_desired_status)

        docker_entrypoint = cast(list[str], d.pop("dockerEntrypoint", UNSET))

        docker_start_cmd = cast(list[str], d.pop("dockerStartCmd", UNSET))

        endpoint_id = d.pop("endpointId", UNSET)

        _env = d.pop("env", UNSET)
        env: PodEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = PodEnv.from_dict(_env)

        _gpu = d.pop("gpu", UNSET)
        gpu: PodGpu | Unset
        if isinstance(_gpu, Unset):
            gpu = UNSET
        else:
            gpu = PodGpu.from_dict(_gpu)

        id = d.pop("id", UNSET)

        image = d.pop("image", UNSET)

        interruptible = d.pop("interruptible", UNSET)

        last_started_at = d.pop("lastStartedAt", UNSET)

        last_status_change = d.pop("lastStatusChange", UNSET)

        locked = d.pop("locked", UNSET)

        _machine = d.pop("machine", UNSET)
        machine: PodMachine | Unset
        if isinstance(_machine, Unset):
            machine = UNSET
        else:
            machine = PodMachine.from_dict(_machine)

        machine_id = d.pop("machineId", UNSET)

        memory_in_gb = d.pop("memoryInGb", UNSET)

        name = d.pop("name", UNSET)

        _network_volume = d.pop("networkVolume", UNSET)
        network_volume: PodNetworkVolume | Unset
        if isinstance(_network_volume, Unset):
            network_volume = UNSET
        else:
            network_volume = PodNetworkVolume.from_dict(_network_volume)

        def _parse_port_mappings(data: object) -> None | PodPortMappingsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                port_mappings_type_0 = PodPortMappingsType0.from_dict(data)

                return port_mappings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | PodPortMappingsType0 | Unset, data)

        port_mappings = _parse_port_mappings(d.pop("portMappings", UNSET))

        ports = cast(list[str], d.pop("ports", UNSET))

        def _parse_public_ip(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        public_ip = _parse_public_ip(d.pop("publicIp", UNSET))

        _savings_plans = d.pop("savingsPlans", UNSET)
        savings_plans: list[SavingsPlan] | Unset = UNSET
        if _savings_plans is not UNSET:
            savings_plans = []
            for savings_plans_item_data in _savings_plans:
                savings_plans_item = SavingsPlan.from_dict(savings_plans_item_data)

                savings_plans.append(savings_plans_item)

        sls_version = d.pop("slsVersion", UNSET)

        template_id = d.pop("templateId", UNSET)

        vcpu_count = d.pop("vcpuCount", UNSET)

        volume_encrypted = d.pop("volumeEncrypted", UNSET)

        volume_in_gb = d.pop("volumeInGb", UNSET)

        volume_mount_path = d.pop("volumeMountPath", UNSET)

        pod = cls(
            adjusted_cost_per_hr=adjusted_cost_per_hr,
            ai_api_id=ai_api_id,
            consumer_user_id=consumer_user_id,
            container_disk_in_gb=container_disk_in_gb,
            container_registry_auth_id=container_registry_auth_id,
            cost_per_hr=cost_per_hr,
            cpu_flavor_id=cpu_flavor_id,
            desired_status=desired_status,
            docker_entrypoint=docker_entrypoint,
            docker_start_cmd=docker_start_cmd,
            endpoint_id=endpoint_id,
            env=env,
            gpu=gpu,
            id=id,
            image=image,
            interruptible=interruptible,
            last_started_at=last_started_at,
            last_status_change=last_status_change,
            locked=locked,
            machine=machine,
            machine_id=machine_id,
            memory_in_gb=memory_in_gb,
            name=name,
            network_volume=network_volume,
            port_mappings=port_mappings,
            ports=ports,
            public_ip=public_ip,
            savings_plans=savings_plans,
            sls_version=sls_version,
            template_id=template_id,
            vcpu_count=vcpu_count,
            volume_encrypted=volume_encrypted,
            volume_in_gb=volume_in_gb,
            volume_mount_path=volume_mount_path,
        )

        pod.additional_properties = d
        return pod

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
