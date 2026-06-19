from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.endpoint_update_in_place_input_scaler_type import EndpointUpdateInPlaceInputScalerType
from ..types import UNSET, Unset

T = TypeVar("T", bound="EndpointUpdateInPlaceInput")


@_attrs_define
class EndpointUpdateInPlaceInput:
    """
    Attributes:
        execution_timeout_ms (int | Unset): The maximum number of milliseconds an individual request can run on a
            Serverless endpoint before the worker is stopped and the request is marked as failed. Example: 600000.
        flashboot (bool | Unset): Whether to use flash boot for the created Serverless endpoint. Example: True.
        idle_timeout (int | Unset): The number of seconds a worker on the created Serverless endpoint can run without
            taking a job before the worker is scaled down. Default: 5.
        name (str | Unset): A user-defined name for a Serverless endpoint. The name does not need to be unique. Example:
            my endpoint.
        scaler_type (EndpointUpdateInPlaceInputScalerType | Unset): The method used to scale up workers on the created
            Serverless endpoint. If QUEUE_DELAY, workers are scaled based on a periodic check to see if any requests have
            been in queue for too long. If REQUEST_COUNT, the desired number of workers is periodically calculated based on
            the number of requests in the endpoint's queue. Use QUEUE_DELAY if you need to ensure requests take no longer
            than a maximum latency, and use REQUEST_COUNT if you need to scale based on the number of requests. Default:
            EndpointUpdateInPlaceInputScalerType.QUEUE_DELAY.
        scaler_value (int | Unset): If the endpoint scalerType is QUEUE_DELAY, the number of seconds a request can
            remain in queue before a new worker is scaled up. If the endpoint scalerType is REQUEST_COUNT, the number of
            workers is increased as needed to meet the number of requests in the endpoint's queue divided by scalerValue.
            Default: 4.
        workers_max (int | Unset): The maximum number of workers that can be running at the same time on a Serverless
            endpoint. Example: 3.
        workers_min (int | Unset): The minimum number of workers that will run at the same time on a Serverless
            endpoint. This number of workers will always stay running for the endpoint, and will be charged even if no
            requests are being processed, but they are charged at a lower rate than running autoscaling workers.
    """

    execution_timeout_ms: int | Unset = UNSET
    flashboot: bool | Unset = UNSET
    idle_timeout: int | Unset = 5
    name: str | Unset = UNSET
    scaler_type: EndpointUpdateInPlaceInputScalerType | Unset = EndpointUpdateInPlaceInputScalerType.QUEUE_DELAY
    scaler_value: int | Unset = 4
    workers_max: int | Unset = UNSET
    workers_min: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        execution_timeout_ms = self.execution_timeout_ms

        flashboot = self.flashboot

        idle_timeout = self.idle_timeout

        name = self.name

        scaler_type: str | Unset = UNSET
        if not isinstance(self.scaler_type, Unset):
            scaler_type = self.scaler_type.value

        scaler_value = self.scaler_value

        workers_max = self.workers_max

        workers_min = self.workers_min

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if execution_timeout_ms is not UNSET:
            field_dict["executionTimeoutMs"] = execution_timeout_ms
        if flashboot is not UNSET:
            field_dict["flashboot"] = flashboot
        if idle_timeout is not UNSET:
            field_dict["idleTimeout"] = idle_timeout
        if name is not UNSET:
            field_dict["name"] = name
        if scaler_type is not UNSET:
            field_dict["scalerType"] = scaler_type
        if scaler_value is not UNSET:
            field_dict["scalerValue"] = scaler_value
        if workers_max is not UNSET:
            field_dict["workersMax"] = workers_max
        if workers_min is not UNSET:
            field_dict["workersMin"] = workers_min

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        execution_timeout_ms = d.pop("executionTimeoutMs", UNSET)

        flashboot = d.pop("flashboot", UNSET)

        idle_timeout = d.pop("idleTimeout", UNSET)

        name = d.pop("name", UNSET)

        _scaler_type = d.pop("scalerType", UNSET)
        scaler_type: EndpointUpdateInPlaceInputScalerType | Unset
        if isinstance(_scaler_type, Unset):
            scaler_type = UNSET
        else:
            scaler_type = EndpointUpdateInPlaceInputScalerType(_scaler_type)

        scaler_value = d.pop("scalerValue", UNSET)

        workers_max = d.pop("workersMax", UNSET)

        workers_min = d.pop("workersMin", UNSET)

        endpoint_update_in_place_input = cls(
            execution_timeout_ms=execution_timeout_ms,
            flashboot=flashboot,
            idle_timeout=idle_timeout,
            name=name,
            scaler_type=scaler_type,
            scaler_value=scaler_value,
            workers_max=workers_max,
            workers_min=workers_min,
        )

        endpoint_update_in_place_input.additional_properties = d
        return endpoint_update_in_place_input

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
