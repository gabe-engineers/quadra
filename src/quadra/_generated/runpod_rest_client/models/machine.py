from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.machine_cpu_type import MachineCpuType
    from ..models.machine_gpu_type import MachineGpuType


T = TypeVar("T", bound="Machine")


@_attrs_define
class Machine:
    """
    Attributes:
        cost_per_hr (float | Unset):
        cpu_count (int | Unset):
        cpu_type (MachineCpuType | Unset):
        cpu_type_id (str | Unset):
        current_price_per_gpu (float | Unset):
        data_center_id (str | Unset):
        disk_throughput_m_bps (int | Unset):
        gpu_available (int | Unset):
        gpu_display_name (str | Unset):
        gpu_type (MachineGpuType | Unset):
        gpu_type_id (str | Unset):
        location (str | Unset):
        maintenance_end (str | Unset):
        maintenance_note (str | Unset):
        maintenance_start (str | Unset):
        max_download_speed_mbps (int | Unset):
        max_upload_speed_mbps (int | Unset):
        min_pod_gpu_count (int | Unset):
        note (str | Unset):
        secure_cloud (bool | Unset):
        support_public_ip (bool | Unset):
    """

    cost_per_hr: float | Unset = UNSET
    cpu_count: int | Unset = UNSET
    cpu_type: MachineCpuType | Unset = UNSET
    cpu_type_id: str | Unset = UNSET
    current_price_per_gpu: float | Unset = UNSET
    data_center_id: str | Unset = UNSET
    disk_throughput_m_bps: int | Unset = UNSET
    gpu_available: int | Unset = UNSET
    gpu_display_name: str | Unset = UNSET
    gpu_type: MachineGpuType | Unset = UNSET
    gpu_type_id: str | Unset = UNSET
    location: str | Unset = UNSET
    maintenance_end: str | Unset = UNSET
    maintenance_note: str | Unset = UNSET
    maintenance_start: str | Unset = UNSET
    max_download_speed_mbps: int | Unset = UNSET
    max_upload_speed_mbps: int | Unset = UNSET
    min_pod_gpu_count: int | Unset = UNSET
    note: str | Unset = UNSET
    secure_cloud: bool | Unset = UNSET
    support_public_ip: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cost_per_hr = self.cost_per_hr

        cpu_count = self.cpu_count

        cpu_type: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cpu_type, Unset):
            cpu_type = self.cpu_type.to_dict()

        cpu_type_id = self.cpu_type_id

        current_price_per_gpu = self.current_price_per_gpu

        data_center_id = self.data_center_id

        disk_throughput_m_bps = self.disk_throughput_m_bps

        gpu_available = self.gpu_available

        gpu_display_name = self.gpu_display_name

        gpu_type: dict[str, Any] | Unset = UNSET
        if not isinstance(self.gpu_type, Unset):
            gpu_type = self.gpu_type.to_dict()

        gpu_type_id = self.gpu_type_id

        location = self.location

        maintenance_end = self.maintenance_end

        maintenance_note = self.maintenance_note

        maintenance_start = self.maintenance_start

        max_download_speed_mbps = self.max_download_speed_mbps

        max_upload_speed_mbps = self.max_upload_speed_mbps

        min_pod_gpu_count = self.min_pod_gpu_count

        note = self.note

        secure_cloud = self.secure_cloud

        support_public_ip = self.support_public_ip

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cost_per_hr is not UNSET:
            field_dict["costPerHr"] = cost_per_hr
        if cpu_count is not UNSET:
            field_dict["cpuCount"] = cpu_count
        if cpu_type is not UNSET:
            field_dict["cpuType"] = cpu_type
        if cpu_type_id is not UNSET:
            field_dict["cpuTypeId"] = cpu_type_id
        if current_price_per_gpu is not UNSET:
            field_dict["currentPricePerGpu"] = current_price_per_gpu
        if data_center_id is not UNSET:
            field_dict["dataCenterId"] = data_center_id
        if disk_throughput_m_bps is not UNSET:
            field_dict["diskThroughputMBps"] = disk_throughput_m_bps
        if gpu_available is not UNSET:
            field_dict["gpuAvailable"] = gpu_available
        if gpu_display_name is not UNSET:
            field_dict["gpuDisplayName"] = gpu_display_name
        if gpu_type is not UNSET:
            field_dict["gpuType"] = gpu_type
        if gpu_type_id is not UNSET:
            field_dict["gpuTypeId"] = gpu_type_id
        if location is not UNSET:
            field_dict["location"] = location
        if maintenance_end is not UNSET:
            field_dict["maintenanceEnd"] = maintenance_end
        if maintenance_note is not UNSET:
            field_dict["maintenanceNote"] = maintenance_note
        if maintenance_start is not UNSET:
            field_dict["maintenanceStart"] = maintenance_start
        if max_download_speed_mbps is not UNSET:
            field_dict["maxDownloadSpeedMbps"] = max_download_speed_mbps
        if max_upload_speed_mbps is not UNSET:
            field_dict["maxUploadSpeedMbps"] = max_upload_speed_mbps
        if min_pod_gpu_count is not UNSET:
            field_dict["minPodGpuCount"] = min_pod_gpu_count
        if note is not UNSET:
            field_dict["note"] = note
        if secure_cloud is not UNSET:
            field_dict["secureCloud"] = secure_cloud
        if support_public_ip is not UNSET:
            field_dict["supportPublicIp"] = support_public_ip

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.machine_cpu_type import MachineCpuType
        from ..models.machine_gpu_type import MachineGpuType

        d = dict(src_dict)
        cost_per_hr = d.pop("costPerHr", UNSET)

        cpu_count = d.pop("cpuCount", UNSET)

        _cpu_type = d.pop("cpuType", UNSET)
        cpu_type: MachineCpuType | Unset
        if isinstance(_cpu_type, Unset):
            cpu_type = UNSET
        else:
            cpu_type = MachineCpuType.from_dict(_cpu_type)

        cpu_type_id = d.pop("cpuTypeId", UNSET)

        current_price_per_gpu = d.pop("currentPricePerGpu", UNSET)

        data_center_id = d.pop("dataCenterId", UNSET)

        disk_throughput_m_bps = d.pop("diskThroughputMBps", UNSET)

        gpu_available = d.pop("gpuAvailable", UNSET)

        gpu_display_name = d.pop("gpuDisplayName", UNSET)

        _gpu_type = d.pop("gpuType", UNSET)
        gpu_type: MachineGpuType | Unset
        if isinstance(_gpu_type, Unset):
            gpu_type = UNSET
        else:
            gpu_type = MachineGpuType.from_dict(_gpu_type)

        gpu_type_id = d.pop("gpuTypeId", UNSET)

        location = d.pop("location", UNSET)

        maintenance_end = d.pop("maintenanceEnd", UNSET)

        maintenance_note = d.pop("maintenanceNote", UNSET)

        maintenance_start = d.pop("maintenanceStart", UNSET)

        max_download_speed_mbps = d.pop("maxDownloadSpeedMbps", UNSET)

        max_upload_speed_mbps = d.pop("maxUploadSpeedMbps", UNSET)

        min_pod_gpu_count = d.pop("minPodGpuCount", UNSET)

        note = d.pop("note", UNSET)

        secure_cloud = d.pop("secureCloud", UNSET)

        support_public_ip = d.pop("supportPublicIp", UNSET)

        machine = cls(
            cost_per_hr=cost_per_hr,
            cpu_count=cpu_count,
            cpu_type=cpu_type,
            cpu_type_id=cpu_type_id,
            current_price_per_gpu=current_price_per_gpu,
            data_center_id=data_center_id,
            disk_throughput_m_bps=disk_throughput_m_bps,
            gpu_available=gpu_available,
            gpu_display_name=gpu_display_name,
            gpu_type=gpu_type,
            gpu_type_id=gpu_type_id,
            location=location,
            maintenance_end=maintenance_end,
            maintenance_note=maintenance_note,
            maintenance_start=maintenance_start,
            max_download_speed_mbps=max_download_speed_mbps,
            max_upload_speed_mbps=max_upload_speed_mbps,
            min_pod_gpu_count=min_pod_gpu_count,
            note=note,
            secure_cloud=secure_cloud,
            support_public_ip=support_public_ip,
        )

        machine.additional_properties = d
        return machine

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
