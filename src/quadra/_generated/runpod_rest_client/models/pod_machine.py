from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pod_machine_cpu_type import PodMachineCpuType
    from ..models.pod_machine_gpu_type import PodMachineGpuType


T = TypeVar("T", bound="PodMachine")


@_attrs_define
class PodMachine:
    """Information about the machine a Pod is running on (see [Machine](#/components/schemas/Machine)).

    Attributes:
        min_pod_gpu_count (int | Unset):
        gpu_type_id (str | Unset):
        gpu_type (PodMachineGpuType | Unset):
        cpu_count (int | Unset):
        cpu_type_id (str | Unset):
        cpu_type (PodMachineCpuType | Unset):
        location (str | Unset):
        data_center_id (str | Unset):
        disk_throughput_m_bps (int | Unset):
        max_download_speed_mbps (int | Unset):
        max_upload_speed_mbps (int | Unset):
        support_public_ip (bool | Unset):
        secure_cloud (bool | Unset):
        maintenance_start (str | Unset):
        maintenance_end (str | Unset):
        maintenance_note (str | Unset):
        note (str | Unset):
        cost_per_hr (float | Unset):
        current_price_per_gpu (float | Unset):
        gpu_available (int | Unset):
        gpu_display_name (str | Unset):
    """

    min_pod_gpu_count: int | Unset = UNSET
    gpu_type_id: str | Unset = UNSET
    gpu_type: PodMachineGpuType | Unset = UNSET
    cpu_count: int | Unset = UNSET
    cpu_type_id: str | Unset = UNSET
    cpu_type: PodMachineCpuType | Unset = UNSET
    location: str | Unset = UNSET
    data_center_id: str | Unset = UNSET
    disk_throughput_m_bps: int | Unset = UNSET
    max_download_speed_mbps: int | Unset = UNSET
    max_upload_speed_mbps: int | Unset = UNSET
    support_public_ip: bool | Unset = UNSET
    secure_cloud: bool | Unset = UNSET
    maintenance_start: str | Unset = UNSET
    maintenance_end: str | Unset = UNSET
    maintenance_note: str | Unset = UNSET
    note: str | Unset = UNSET
    cost_per_hr: float | Unset = UNSET
    current_price_per_gpu: float | Unset = UNSET
    gpu_available: int | Unset = UNSET
    gpu_display_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        min_pod_gpu_count = self.min_pod_gpu_count

        gpu_type_id = self.gpu_type_id

        gpu_type: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gpu_type, Unset):
            gpu_type = self.gpu_type.to_dict()

        cpu_count = self.cpu_count

        cpu_type_id = self.cpu_type_id

        cpu_type: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cpu_type, Unset):
            cpu_type = self.cpu_type.to_dict()

        location = self.location

        data_center_id = self.data_center_id

        disk_throughput_m_bps = self.disk_throughput_m_bps

        max_download_speed_mbps = self.max_download_speed_mbps

        max_upload_speed_mbps = self.max_upload_speed_mbps

        support_public_ip = self.support_public_ip

        secure_cloud = self.secure_cloud

        maintenance_start = self.maintenance_start

        maintenance_end = self.maintenance_end

        maintenance_note = self.maintenance_note

        note = self.note

        cost_per_hr = self.cost_per_hr

        current_price_per_gpu = self.current_price_per_gpu

        gpu_available = self.gpu_available

        gpu_display_name = self.gpu_display_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if min_pod_gpu_count is not UNSET:
            field_dict["minPodGpuCount"] = min_pod_gpu_count
        if gpu_type_id is not UNSET:
            field_dict["gpuTypeId"] = gpu_type_id
        if gpu_type is not UNSET:
            field_dict["gpuType"] = gpu_type
        if cpu_count is not UNSET:
            field_dict["cpuCount"] = cpu_count
        if cpu_type_id is not UNSET:
            field_dict["cpuTypeId"] = cpu_type_id
        if cpu_type is not UNSET:
            field_dict["cpuType"] = cpu_type
        if location is not UNSET:
            field_dict["location"] = location
        if data_center_id is not UNSET:
            field_dict["dataCenterId"] = data_center_id
        if disk_throughput_m_bps is not UNSET:
            field_dict["diskThroughputMBps"] = disk_throughput_m_bps
        if max_download_speed_mbps is not UNSET:
            field_dict["maxDownloadSpeedMbps"] = max_download_speed_mbps
        if max_upload_speed_mbps is not UNSET:
            field_dict["maxUploadSpeedMbps"] = max_upload_speed_mbps
        if support_public_ip is not UNSET:
            field_dict["supportPublicIp"] = support_public_ip
        if secure_cloud is not UNSET:
            field_dict["secureCloud"] = secure_cloud
        if maintenance_start is not UNSET:
            field_dict["maintenanceStart"] = maintenance_start
        if maintenance_end is not UNSET:
            field_dict["maintenanceEnd"] = maintenance_end
        if maintenance_note is not UNSET:
            field_dict["maintenanceNote"] = maintenance_note
        if note is not UNSET:
            field_dict["note"] = note
        if cost_per_hr is not UNSET:
            field_dict["costPerHr"] = cost_per_hr
        if current_price_per_gpu is not UNSET:
            field_dict["currentPricePerGpu"] = current_price_per_gpu
        if gpu_available is not UNSET:
            field_dict["gpuAvailable"] = gpu_available
        if gpu_display_name is not UNSET:
            field_dict["gpuDisplayName"] = gpu_display_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pod_machine_cpu_type import PodMachineCpuType
        from ..models.pod_machine_gpu_type import PodMachineGpuType

        d = dict(src_dict)
        min_pod_gpu_count = d.pop("minPodGpuCount", UNSET)

        gpu_type_id = d.pop("gpuTypeId", UNSET)

        _gpu_type = d.pop("gpuType", UNSET)
        gpu_type: PodMachineGpuType | Unset
        if isinstance(_gpu_type, Unset):
            gpu_type = UNSET
        else:
            gpu_type = PodMachineGpuType.from_dict(_gpu_type)

        cpu_count = d.pop("cpuCount", UNSET)

        cpu_type_id = d.pop("cpuTypeId", UNSET)

        _cpu_type = d.pop("cpuType", UNSET)
        cpu_type: PodMachineCpuType | Unset
        if isinstance(_cpu_type, Unset):
            cpu_type = UNSET
        else:
            cpu_type = PodMachineCpuType.from_dict(_cpu_type)

        location = d.pop("location", UNSET)

        data_center_id = d.pop("dataCenterId", UNSET)

        disk_throughput_m_bps = d.pop("diskThroughputMBps", UNSET)

        max_download_speed_mbps = d.pop("maxDownloadSpeedMbps", UNSET)

        max_upload_speed_mbps = d.pop("maxUploadSpeedMbps", UNSET)

        support_public_ip = d.pop("supportPublicIp", UNSET)

        secure_cloud = d.pop("secureCloud", UNSET)

        maintenance_start = d.pop("maintenanceStart", UNSET)

        maintenance_end = d.pop("maintenanceEnd", UNSET)

        maintenance_note = d.pop("maintenanceNote", UNSET)

        note = d.pop("note", UNSET)

        cost_per_hr = d.pop("costPerHr", UNSET)

        current_price_per_gpu = d.pop("currentPricePerGpu", UNSET)

        gpu_available = d.pop("gpuAvailable", UNSET)

        gpu_display_name = d.pop("gpuDisplayName", UNSET)

        pod_machine = cls(
            min_pod_gpu_count=min_pod_gpu_count,
            gpu_type_id=gpu_type_id,
            gpu_type=gpu_type,
            cpu_count=cpu_count,
            cpu_type_id=cpu_type_id,
            cpu_type=cpu_type,
            location=location,
            data_center_id=data_center_id,
            disk_throughput_m_bps=disk_throughput_m_bps,
            max_download_speed_mbps=max_download_speed_mbps,
            max_upload_speed_mbps=max_upload_speed_mbps,
            support_public_ip=support_public_ip,
            secure_cloud=secure_cloud,
            maintenance_start=maintenance_start,
            maintenance_end=maintenance_end,
            maintenance_note=maintenance_note,
            note=note,
            cost_per_hr=cost_per_hr,
            current_price_per_gpu=current_price_per_gpu,
            gpu_available=gpu_available,
            gpu_display_name=gpu_display_name,
        )

        pod_machine.additional_properties = d
        return pod_machine

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
