from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.endpoint_create_input_allowed_cuda_versions_item import EndpointCreateInputAllowedCudaVersionsItem
from ..models.endpoint_create_input_compute_type import EndpointCreateInputComputeType
from ..models.endpoint_create_input_cpu_flavor_ids_item import EndpointCreateInputCpuFlavorIdsItem
from ..models.endpoint_create_input_data_center_ids_item import EndpointCreateInputDataCenterIdsItem
from ..models.endpoint_create_input_gpu_type_ids_item import EndpointCreateInputGpuTypeIdsItem
from ..models.endpoint_create_input_min_cuda_version import EndpointCreateInputMinCudaVersion
from ..models.endpoint_create_input_scaler_type import EndpointCreateInputScalerType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointCreateInput")


@_attrs_define
class EndpointCreateInput:
    """
    Attributes:
        template_id (str): The unique string identifying the template used to create the Serverless endpoint. Example:
            30zmvf89kd.
        allowed_cuda_versions (list[EndpointCreateInputAllowedCudaVersionsItem] | Unset): If the created Serverless
            endpoint is a GPU endpoint, a list of acceptable CUDA versions on the created workers. If not set, any CUDA
            version is acceptable.
        compute_type (EndpointCreateInputComputeType | Unset): Set to GPU to create a Serverless endpoint with GPU
            workers. Set to CPU to create a Serverless endpoint with CPU workers. If set to CPU, properties related to GPUs
            such as gpuTypeIds will be ignored. If set to GPU, properties related to CPUs such as cpuFlavorIds will be
            ignored. Default: EndpointCreateInputComputeType.GPU.
        cpu_flavor_ids (list[EndpointCreateInputCpuFlavorIdsItem] | Unset): If the created Serverless endpoint is a CPU
            endpoint, a list of Runpod CPU flavors which can be attached to the created workers. The order of the list
            determines the order to rent CPU flavors.
        data_center_ids (list[EndpointCreateInputDataCenterIdsItem] | Unset): A list of Runpod data center IDs where
            workers on the created Serverless endpoint can be located. Example: ['EU-RO-1', 'CA-MTL-1'].
        execution_timeout_ms (int | Unset): The maximum number of milliseconds an individual request can run on a
            Serverless endpoint before the worker is stopped and the request is marked as failed. Example: 600000.
        flashboot (bool | Unset): Whether to use flash boot for the created Serverless endpoint. Example: True.
        gpu_count (int | Unset): If the created Serverless endpoint is a GPU endpoint, the number of GPUs attached to
            each worker on the endpoint. Default: 1.
        gpu_type_ids (list[EndpointCreateInputGpuTypeIdsItem] | Unset): If the created Serverless endpoint is a GPU
            endpoint, a list of Runpod GPU types which can be attached to the created workers. The order of the list
            determines the order to rent GPU types.
        idle_timeout (int | Unset): The number of seconds a worker on the created Serverless endpoint can run without
            taking a job before the worker is scaled down. Default: 5.
        min_cuda_version (EndpointCreateInputMinCudaVersion | Unset): If the created Serverless endpoint is a GPU
            endpoint, the minimum acceptable CUDA version on the created workers.
        name (str | Unset): A user-defined name for the created Serverless endpoint. The name does not need to be
            unique.
        network_volume_id (str | Unset): The unique string identifying the network volume to attach to the created
            Serverless endpoint.
        network_volume_ids (list[str] | Unset): A list of network volume IDs to attach to the created Serverless
            endpoint. Allows multiple network volumes to be used with multi-region endpoints.
        scaler_type (EndpointCreateInputScalerType | Unset): The method used to scale up workers on the created
            Serverless endpoint. If QUEUE_DELAY, workers are scaled based on a periodic check to see if any requests have
            been in queue for too long. If REQUEST_COUNT, the desired number of workers is periodically calculated based on
            the number of requests in the endpoint's queue. Use QUEUE_DELAY if you need to ensure requests take no longer
            than a maximum latency, and use REQUEST_COUNT if you need to scale based on the number of requests. Default:
            EndpointCreateInputScalerType.QUEUE_DELAY.
        scaler_value (int | Unset): If the endpoint scalerType is QUEUE_DELAY, the number of seconds a request can
            remain in queue before a new worker is scaled up. If the endpoint scalerType is REQUEST_COUNT, the number of
            workers is increased as needed to meet the number of requests in the endpoint's queue divided by scalerValue.
            Default: 4.
        vcpu_count (int | Unset): If the created Serverless endpoint is a CPU endpoint, the number of vCPUs allocated to
            each created worker. Default: 2.
        workers_max (int | Unset): The maximum number of workers that can be running at the same time on a Serverless
            endpoint. Example: 3.
        workers_min (int | Unset): The minimum number of workers that will run at the same time on a Serverless
            endpoint. This number of workers will always stay running for the endpoint, and will be charged even if no
            requests are being processed, but they are charged at a lower rate than running autoscaling workers.
    """

    template_id: str
    allowed_cuda_versions: list[EndpointCreateInputAllowedCudaVersionsItem] | Unset = UNSET
    compute_type: EndpointCreateInputComputeType | Unset = EndpointCreateInputComputeType.GPU
    cpu_flavor_ids: list[EndpointCreateInputCpuFlavorIdsItem] | Unset = UNSET
    data_center_ids: list[EndpointCreateInputDataCenterIdsItem] | Unset = UNSET
    execution_timeout_ms: int | Unset = UNSET
    flashboot: bool | Unset = UNSET
    gpu_count: int | Unset = 1
    gpu_type_ids: list[EndpointCreateInputGpuTypeIdsItem] | Unset = UNSET
    idle_timeout: int | Unset = 5
    min_cuda_version: EndpointCreateInputMinCudaVersion | Unset = UNSET
    name: str | Unset = UNSET
    network_volume_id: str | Unset = UNSET
    network_volume_ids: list[str] | Unset = UNSET
    scaler_type: EndpointCreateInputScalerType | Unset = EndpointCreateInputScalerType.QUEUE_DELAY
    scaler_value: int | Unset = 4
    vcpu_count: int | Unset = 2
    workers_max: int | Unset = UNSET
    workers_min: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = self.template_id

        allowed_cuda_versions: list[str] | Unset = UNSET
        if not isinstance(self.allowed_cuda_versions, Unset):
            allowed_cuda_versions = []
            for allowed_cuda_versions_item_data in self.allowed_cuda_versions:
                allowed_cuda_versions_item = allowed_cuda_versions_item_data.value
                allowed_cuda_versions.append(allowed_cuda_versions_item)

        compute_type: str | Unset = UNSET
        if not isinstance(self.compute_type, Unset):
            compute_type = self.compute_type.value

        cpu_flavor_ids: list[str] | Unset = UNSET
        if not isinstance(self.cpu_flavor_ids, Unset):
            cpu_flavor_ids = []
            for cpu_flavor_ids_item_data in self.cpu_flavor_ids:
                cpu_flavor_ids_item = cpu_flavor_ids_item_data.value
                cpu_flavor_ids.append(cpu_flavor_ids_item)

        data_center_ids: list[str] | Unset = UNSET
        if not isinstance(self.data_center_ids, Unset):
            data_center_ids = []
            for data_center_ids_item_data in self.data_center_ids:
                data_center_ids_item = data_center_ids_item_data.value
                data_center_ids.append(data_center_ids_item)

        execution_timeout_ms = self.execution_timeout_ms

        flashboot = self.flashboot

        gpu_count = self.gpu_count

        gpu_type_ids: list[str] | Unset = UNSET
        if not isinstance(self.gpu_type_ids, Unset):
            gpu_type_ids = []
            for gpu_type_ids_item_data in self.gpu_type_ids:
                gpu_type_ids_item = gpu_type_ids_item_data.value
                gpu_type_ids.append(gpu_type_ids_item)

        idle_timeout = self.idle_timeout

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

        vcpu_count = self.vcpu_count

        workers_max = self.workers_max

        workers_min = self.workers_min

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "templateId": template_id,
            }
        )
        if allowed_cuda_versions is not UNSET:
            field_dict["allowedCudaVersions"] = allowed_cuda_versions
        if compute_type is not UNSET:
            field_dict["computeType"] = compute_type
        if cpu_flavor_ids is not UNSET:
            field_dict["cpuFlavorIds"] = cpu_flavor_ids
        if data_center_ids is not UNSET:
            field_dict["dataCenterIds"] = data_center_ids
        if execution_timeout_ms is not UNSET:
            field_dict["executionTimeoutMs"] = execution_timeout_ms
        if flashboot is not UNSET:
            field_dict["flashboot"] = flashboot
        if gpu_count is not UNSET:
            field_dict["gpuCount"] = gpu_count
        if gpu_type_ids is not UNSET:
            field_dict["gpuTypeIds"] = gpu_type_ids
        if idle_timeout is not UNSET:
            field_dict["idleTimeout"] = idle_timeout
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
        if vcpu_count is not UNSET:
            field_dict["vcpuCount"] = vcpu_count
        if workers_max is not UNSET:
            field_dict["workersMax"] = workers_max
        if workers_min is not UNSET:
            field_dict["workersMin"] = workers_min

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        template_id = d.pop("templateId")

        _allowed_cuda_versions = d.pop("allowedCudaVersions", UNSET)
        allowed_cuda_versions: list[EndpointCreateInputAllowedCudaVersionsItem] | Unset = UNSET
        if _allowed_cuda_versions is not UNSET:
            allowed_cuda_versions = []
            for allowed_cuda_versions_item_data in _allowed_cuda_versions:
                allowed_cuda_versions_item = EndpointCreateInputAllowedCudaVersionsItem(allowed_cuda_versions_item_data)

                allowed_cuda_versions.append(allowed_cuda_versions_item)

        _compute_type = d.pop("computeType", UNSET)
        compute_type: EndpointCreateInputComputeType | Unset
        if isinstance(_compute_type, Unset):
            compute_type = UNSET
        else:
            compute_type = EndpointCreateInputComputeType(_compute_type)

        _cpu_flavor_ids = d.pop("cpuFlavorIds", UNSET)
        cpu_flavor_ids: list[EndpointCreateInputCpuFlavorIdsItem] | Unset = UNSET
        if _cpu_flavor_ids is not UNSET:
            cpu_flavor_ids = []
            for cpu_flavor_ids_item_data in _cpu_flavor_ids:
                cpu_flavor_ids_item = EndpointCreateInputCpuFlavorIdsItem(cpu_flavor_ids_item_data)

                cpu_flavor_ids.append(cpu_flavor_ids_item)

        _data_center_ids = d.pop("dataCenterIds", UNSET)
        data_center_ids: list[EndpointCreateInputDataCenterIdsItem] | Unset = UNSET
        if _data_center_ids is not UNSET:
            data_center_ids = []
            for data_center_ids_item_data in _data_center_ids:
                data_center_ids_item = EndpointCreateInputDataCenterIdsItem(data_center_ids_item_data)

                data_center_ids.append(data_center_ids_item)

        execution_timeout_ms = d.pop("executionTimeoutMs", UNSET)

        flashboot = d.pop("flashboot", UNSET)

        gpu_count = d.pop("gpuCount", UNSET)

        _gpu_type_ids = d.pop("gpuTypeIds", UNSET)
        gpu_type_ids: list[EndpointCreateInputGpuTypeIdsItem] | Unset = UNSET
        if _gpu_type_ids is not UNSET:
            gpu_type_ids = []
            for gpu_type_ids_item_data in _gpu_type_ids:
                gpu_type_ids_item = EndpointCreateInputGpuTypeIdsItem(gpu_type_ids_item_data)

                gpu_type_ids.append(gpu_type_ids_item)

        idle_timeout = d.pop("idleTimeout", UNSET)

        _min_cuda_version = d.pop("minCudaVersion", UNSET)
        min_cuda_version: EndpointCreateInputMinCudaVersion | Unset
        if isinstance(_min_cuda_version, Unset):
            min_cuda_version = UNSET
        else:
            min_cuda_version = EndpointCreateInputMinCudaVersion(_min_cuda_version)

        name = d.pop("name", UNSET)

        network_volume_id = d.pop("networkVolumeId", UNSET)

        network_volume_ids = cast(list[str], d.pop("networkVolumeIds", UNSET))

        _scaler_type = d.pop("scalerType", UNSET)
        scaler_type: EndpointCreateInputScalerType | Unset
        if isinstance(_scaler_type, Unset):
            scaler_type = UNSET
        else:
            scaler_type = EndpointCreateInputScalerType(_scaler_type)

        scaler_value = d.pop("scalerValue", UNSET)

        vcpu_count = d.pop("vcpuCount", UNSET)

        workers_max = d.pop("workersMax", UNSET)

        workers_min = d.pop("workersMin", UNSET)

        endpoint_create_input = cls(
            template_id=template_id,
            allowed_cuda_versions=allowed_cuda_versions,
            compute_type=compute_type,
            cpu_flavor_ids=cpu_flavor_ids,
            data_center_ids=data_center_ids,
            execution_timeout_ms=execution_timeout_ms,
            flashboot=flashboot,
            gpu_count=gpu_count,
            gpu_type_ids=gpu_type_ids,
            idle_timeout=idle_timeout,
            min_cuda_version=min_cuda_version,
            name=name,
            network_volume_id=network_volume_id,
            network_volume_ids=network_volume_ids,
            scaler_type=scaler_type,
            scaler_value=scaler_value,
            vcpu_count=vcpu_count,
            workers_max=workers_max,
            workers_min=workers_min,
        )

        endpoint_create_input.additional_properties = d
        return endpoint_create_input

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
