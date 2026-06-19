from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.endpoint_allowed_cuda_versions_item import EndpointAllowedCudaVersionsItem
from ..models.endpoint_compute_type import EndpointComputeType
from ..models.endpoint_data_center_ids_item import EndpointDataCenterIdsItem
from ..models.endpoint_gpu_type_ids_item import EndpointGpuTypeIdsItem
from ..models.endpoint_min_cuda_version import EndpointMinCudaVersion
from ..models.endpoint_scaler_type import EndpointScalerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.endpoint_env import EndpointEnv
    from ..models.pod import Pod
    from ..models.template import Template


T = TypeVar("T", bound="Endpoint")


@_attrs_define
class Endpoint:
    """
    Attributes:
        allowed_cuda_versions (list[EndpointAllowedCudaVersionsItem] | Unset): A list of acceptable CUDA versions for
            the workers on a Serverless endpoint. If not set, any CUDA version is acceptable.
        compute_type (EndpointComputeType | Unset): The type of compute used by workers on a Serverless endpoint.
            Example: GPU.
        created_at (str | Unset): The UTC timestamp when a Serverless endpoint was created. Example:
            2024-07-12T19:14:40.144Z.
        data_center_ids (list[EndpointDataCenterIdsItem] | Unset): A list of Runpod data center IDs where workers on a
            Serverless endpoint can be located. Example: EU-NL-1,EU-RO-1,EU-SE-1.
        env (EndpointEnv | Unset):  Example: {'ENV_VAR': 'value'}.
        execution_timeout_ms (int | Unset): The maximum number of milliseconds an individual request can run on a
            Serverless endpoint before the worker is stopped and the request is marked as failed. Example: 600000.
        gpu_count (int | Unset): The number of GPUs attached to each worker on a Serverless endpoint. Example: 1.
        gpu_type_ids (list[EndpointGpuTypeIdsItem] | Unset): A list of Runpod GPU types which can be attached to a
            Serverless endpoint.
        id (str | Unset): A unique string identifying a Serverless endpoint. Example: jpnw0v75y3qoql.
        idle_timeout (int | Unset): The number of seconds a worker on a Serverless endpoint can be running without
            taking a job before the worker is scaled down. Example: 5.
        instance_ids (list[str] | Unset): For CPU Serverless endpoints, a list of instance IDs that can be attached to a
            Serverless endpoint. Example: ['cpu3c-8-16'].
        min_cuda_version (EndpointMinCudaVersion | Unset): The minimum acceptable CUDA version for the workers on a
            Serverless endpoint.
        name (str | Unset): A user-defined name for a Serverless endpoint. The name does not need to be unique. Example:
            my endpoint.
        network_volume_id (str | Unset): The unique string identifying the network volume to attach to the Serverless
            endpoint. Example: agv6w2qcg7.
        network_volume_ids (list[str] | Unset): A list of network volume IDs attached to the Serverless endpoint. Allows
            multiple network volumes to be used with multi-region endpoints. Example: ['agv6w2qcg7', 'bxh7w3rch8'].
        scaler_type (EndpointScalerType | Unset): The method used to scale up workers on a Serverless endpoint. If
            QUEUE_DELAY, workers are scaled based on a periodic check to see if any requests have been in queue for too
            long. If REQUEST_COUNT, the desired number of workers is periodically calculated based on the number of requests
            in the endpoint's queue. Use QUEUE_DELAY if you need to ensure requests take no longer than a maximum latency,
            and use REQUEST_COUNT if you need to scale based on the number of requests. Example: QUEUE_DELAY.
        scaler_value (int | Unset): If the endpoint scalerType is QUEUE_DELAY, the number of seconds a request can
            remain in queue before a new worker is scaled up. If the endpoint scalerType is REQUEST_COUNT, the number of
            workers is increased as needed to meet the number of requests in the endpoint's queue divided by scalerValue.
            Example: 4.
        template (Template | Unset):
        template_id (str | Unset): The unique string identifying the template used to create a Serverless endpoint.
            Example: 30zmvf89kd.
        user_id (str | Unset): A unique string identifying the Runpod user who created a Serverless endpoint. Example:
            user_2PyTJrLzeuwfZilRZ7JhCQDuSqo.
        version (int | Unset): The latest version of a Serverless endpoint, which is updated whenever the template or
            environment variables of the endpoint are changed.
        workers (list[Pod] | Unset): Information about current workers on a Serverless endpoint.
        workers_max (int | Unset): The maximum number of workers that can be running at the same time on a Serverless
            endpoint. Example: 3.
        workers_min (int | Unset): The minimum number of workers that will run at the same time on a Serverless
            endpoint. This number of workers will always stay running for the endpoint, and will be charged even if no
            requests are being processed, but they are charged at a lower rate than running autoscaling workers.
    """

    allowed_cuda_versions: list[EndpointAllowedCudaVersionsItem] | Unset = UNSET
    compute_type: EndpointComputeType | Unset = UNSET
    created_at: str | Unset = UNSET
    data_center_ids: list[EndpointDataCenterIdsItem] | Unset = UNSET
    env: EndpointEnv | Unset = UNSET
    execution_timeout_ms: int | Unset = UNSET
    gpu_count: int | Unset = UNSET
    gpu_type_ids: list[EndpointGpuTypeIdsItem] | Unset = UNSET
    id: str | Unset = UNSET
    idle_timeout: int | Unset = UNSET
    instance_ids: list[str] | Unset = UNSET
    min_cuda_version: EndpointMinCudaVersion | Unset = UNSET
    name: str | Unset = UNSET
    network_volume_id: str | Unset = UNSET
    network_volume_ids: list[str] | Unset = UNSET
    scaler_type: EndpointScalerType | Unset = UNSET
    scaler_value: int | Unset = UNSET
    template: Template | Unset = UNSET
    template_id: str | Unset = UNSET
    user_id: str | Unset = UNSET
    version: int | Unset = UNSET
    workers: list[Pod] | Unset = UNSET
    workers_max: int | Unset = UNSET
    workers_min: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allowed_cuda_versions: list[str] | Unset = UNSET
        if not isinstance(self.allowed_cuda_versions, Unset):
            allowed_cuda_versions = []
            for allowed_cuda_versions_item_data in self.allowed_cuda_versions:
                allowed_cuda_versions_item = allowed_cuda_versions_item_data.value
                allowed_cuda_versions.append(allowed_cuda_versions_item)

        compute_type: str | Unset = UNSET
        if not isinstance(self.compute_type, Unset):
            compute_type = self.compute_type.value

        created_at = self.created_at

        data_center_ids: list[str] | Unset = UNSET
        if not isinstance(self.data_center_ids, Unset):
            data_center_ids = []
            for data_center_ids_item_data in self.data_center_ids:
                data_center_ids_item = data_center_ids_item_data.value
                data_center_ids.append(data_center_ids_item)

        env: dict[str, Any] | Unset = UNSET
        if not isinstance(self.env, Unset):
            env = self.env.to_dict()

        execution_timeout_ms = self.execution_timeout_ms

        gpu_count = self.gpu_count

        gpu_type_ids: list[str] | Unset = UNSET
        if not isinstance(self.gpu_type_ids, Unset):
            gpu_type_ids = []
            for gpu_type_ids_item_data in self.gpu_type_ids:
                gpu_type_ids_item = gpu_type_ids_item_data.value
                gpu_type_ids.append(gpu_type_ids_item)

        id = self.id

        idle_timeout = self.idle_timeout

        instance_ids: list[str] | Unset = UNSET
        if not isinstance(self.instance_ids, Unset):
            instance_ids = self.instance_ids

        min_cuda_version: str | Unset = UNSET
        if not isinstance(self.min_cuda_version, Unset):
            min_cuda_version = self.min_cuda_version.value

        name = self.name

        network_volume_id = self.network_volume_id

        network_volume_ids: list[str] | Unset = UNSET
        if not isinstance(self.network_volume_ids, Unset):
            network_volume_ids = self.network_volume_ids

        scaler_type: str | Unset = UNSET
        if not isinstance(self.scaler_type, Unset):
            scaler_type = self.scaler_type.value

        scaler_value = self.scaler_value

        template: dict[str, Any] | Unset = UNSET
        if not isinstance(self.template, Unset):
            template = self.template.to_dict()

        template_id = self.template_id

        user_id = self.user_id

        version = self.version

        workers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.workers, Unset):
            workers = []
            for workers_item_data in self.workers:
                workers_item = workers_item_data.to_dict()
                workers.append(workers_item)

        workers_max = self.workers_max

        workers_min = self.workers_min

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if allowed_cuda_versions is not UNSET:
            field_dict["allowedCudaVersions"] = allowed_cuda_versions
        if compute_type is not UNSET:
            field_dict["computeType"] = compute_type
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if data_center_ids is not UNSET:
            field_dict["dataCenterIds"] = data_center_ids
        if env is not UNSET:
            field_dict["env"] = env
        if execution_timeout_ms is not UNSET:
            field_dict["executionTimeoutMs"] = execution_timeout_ms
        if gpu_count is not UNSET:
            field_dict["gpuCount"] = gpu_count
        if gpu_type_ids is not UNSET:
            field_dict["gpuTypeIds"] = gpu_type_ids
        if id is not UNSET:
            field_dict["id"] = id
        if idle_timeout is not UNSET:
            field_dict["idleTimeout"] = idle_timeout
        if instance_ids is not UNSET:
            field_dict["instanceIds"] = instance_ids
        if min_cuda_version is not UNSET:
            field_dict["minCudaVersion"] = min_cuda_version
        if name is not UNSET:
            field_dict["name"] = name
        if network_volume_id is not UNSET:
            field_dict["networkVolumeId"] = network_volume_id
        if network_volume_ids is not UNSET:
            field_dict["networkVolumeIds"] = network_volume_ids
        if scaler_type is not UNSET:
            field_dict["scalerType"] = scaler_type
        if scaler_value is not UNSET:
            field_dict["scalerValue"] = scaler_value
        if template is not UNSET:
            field_dict["template"] = template
        if template_id is not UNSET:
            field_dict["templateId"] = template_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if version is not UNSET:
            field_dict["version"] = version
        if workers is not UNSET:
            field_dict["workers"] = workers
        if workers_max is not UNSET:
            field_dict["workersMax"] = workers_max
        if workers_min is not UNSET:
            field_dict["workersMin"] = workers_min

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.endpoint_env import EndpointEnv
        from ..models.pod import Pod
        from ..models.template import Template

        d = dict(src_dict)
        _allowed_cuda_versions = d.pop("allowedCudaVersions", UNSET)
        allowed_cuda_versions: list[EndpointAllowedCudaVersionsItem] | Unset = UNSET
        if _allowed_cuda_versions is not UNSET:
            allowed_cuda_versions = []
            for allowed_cuda_versions_item_data in _allowed_cuda_versions:
                allowed_cuda_versions_item = EndpointAllowedCudaVersionsItem(allowed_cuda_versions_item_data)

                allowed_cuda_versions.append(allowed_cuda_versions_item)

        _compute_type = d.pop("computeType", UNSET)
        compute_type: EndpointComputeType | Unset
        if isinstance(_compute_type, Unset):
            compute_type = UNSET
        else:
            compute_type = EndpointComputeType(_compute_type)

        created_at = d.pop("createdAt", UNSET)

        _data_center_ids = d.pop("dataCenterIds", UNSET)
        data_center_ids: list[EndpointDataCenterIdsItem] | Unset = UNSET
        if _data_center_ids is not UNSET:
            data_center_ids = []
            for data_center_ids_item_data in _data_center_ids:
                data_center_ids_item = EndpointDataCenterIdsItem(data_center_ids_item_data)

                data_center_ids.append(data_center_ids_item)

        _env = d.pop("env", UNSET)
        env: EndpointEnv | Unset
        if isinstance(_env, Unset):
            env = UNSET
        else:
            env = EndpointEnv.from_dict(_env)

        execution_timeout_ms = d.pop("executionTimeoutMs", UNSET)

        gpu_count = d.pop("gpuCount", UNSET)

        _gpu_type_ids = d.pop("gpuTypeIds", UNSET)
        gpu_type_ids: list[EndpointGpuTypeIdsItem] | Unset = UNSET
        if _gpu_type_ids is not UNSET:
            gpu_type_ids = []
            for gpu_type_ids_item_data in _gpu_type_ids:
                gpu_type_ids_item = EndpointGpuTypeIdsItem(gpu_type_ids_item_data)

                gpu_type_ids.append(gpu_type_ids_item)

        id = d.pop("id", UNSET)

        idle_timeout = d.pop("idleTimeout", UNSET)

        instance_ids = cast(list[str], d.pop("instanceIds", UNSET))

        _min_cuda_version = d.pop("minCudaVersion", UNSET)
        min_cuda_version: EndpointMinCudaVersion | Unset
        if isinstance(_min_cuda_version, Unset):
            min_cuda_version = UNSET
        else:
            min_cuda_version = EndpointMinCudaVersion(_min_cuda_version)

        name = d.pop("name", UNSET)

        network_volume_id = d.pop("networkVolumeId", UNSET)

        network_volume_ids = cast(list[str], d.pop("networkVolumeIds", UNSET))

        _scaler_type = d.pop("scalerType", UNSET)
        scaler_type: EndpointScalerType | Unset
        if isinstance(_scaler_type, Unset):
            scaler_type = UNSET
        else:
            scaler_type = EndpointScalerType(_scaler_type)

        scaler_value = d.pop("scalerValue", UNSET)

        _template = d.pop("template", UNSET)
        template: Template | Unset
        if isinstance(_template, Unset):
            template = UNSET
        else:
            template = Template.from_dict(_template)

        template_id = d.pop("templateId", UNSET)

        user_id = d.pop("userId", UNSET)

        version = d.pop("version", UNSET)

        _workers = d.pop("workers", UNSET)
        workers: list[Pod] | Unset = UNSET
        if _workers is not UNSET:
            workers = []
            for workers_item_data in _workers:
                workers_item = Pod.from_dict(workers_item_data)

                workers.append(workers_item)

        workers_max = d.pop("workersMax", UNSET)

        workers_min = d.pop("workersMin", UNSET)

        endpoint = cls(
            allowed_cuda_versions=allowed_cuda_versions,
            compute_type=compute_type,
            created_at=created_at,
            data_center_ids=data_center_ids,
            env=env,
            execution_timeout_ms=execution_timeout_ms,
            gpu_count=gpu_count,
            gpu_type_ids=gpu_type_ids,
            id=id,
            idle_timeout=idle_timeout,
            instance_ids=instance_ids,
            min_cuda_version=min_cuda_version,
            name=name,
            network_volume_id=network_volume_id,
            network_volume_ids=network_volume_ids,
            scaler_type=scaler_type,
            scaler_value=scaler_value,
            template=template,
            template_id=template_id,
            user_id=user_id,
            version=version,
            workers=workers,
            workers_max=workers_max,
            workers_min=workers_min,
        )

        endpoint.additional_properties = d
        return endpoint

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
