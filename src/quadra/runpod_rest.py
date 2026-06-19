from __future__ import annotations

import json
import os
from http import HTTPStatus
from typing import Any, Callable

import httpx

from quadra import __version__
from quadra._generated.runpod_rest_client import AuthenticatedClient
from quadra._generated.runpod_rest_client.api.endpoints import (
    create_endpoint as create_endpoint_api,
)
from quadra._generated.runpod_rest_client.api.endpoints import (
    update_endpoint as update_endpoint_api,
)
from quadra._generated.runpod_rest_client.api.network_volumes import (
    create_network_volume as create_network_volume_api,
)
from quadra._generated.runpod_rest_client.api.network_volumes import (
    list_network_volumes as list_network_volumes_api,
)
from quadra._generated.runpod_rest_client.api.templates import (
    create_template as create_template_api,
)
from quadra._generated.runpod_rest_client.api.templates import (
    get_template as get_template_api,
)
from quadra._generated.runpod_rest_client.api.templates import (
    list_templates as list_templates_api,
)
from quadra._generated.runpod_rest_client.api.templates import (
    update_template as update_template_api,
)
from quadra._generated.runpod_rest_client.errors import UnexpectedStatus
from quadra._generated.runpod_rest_client.models.endpoint_create_input import (
    EndpointCreateInput,
)
from quadra._generated.runpod_rest_client.models.endpoint_create_input_gpu_type_ids_item import (
    EndpointCreateInputGpuTypeIdsItem,
)
from quadra._generated.runpod_rest_client.models.endpoint import Endpoint
from quadra._generated.runpod_rest_client.models.endpoint_update_input import (
    EndpointUpdateInput,
)
from quadra._generated.runpod_rest_client.models.network_volume import NetworkVolume
from quadra._generated.runpod_rest_client.models.network_volume_create_input import (
    NetworkVolumeCreateInput,
)
from quadra._generated.runpod_rest_client.models.network_volumes_item import (
    NetworkVolumesItem,
)
from quadra._generated.runpod_rest_client.models.template import Template
from quadra._generated.runpod_rest_client.models.template_create_input import (
    TemplateCreateInput,
)
from quadra._generated.runpod_rest_client.models.template_update_input import (
    TemplateUpdateInput,
)
from quadra._generated.runpod_rest_client.types import Response
from quadra.errors import QuadraError

DEFAULT_RUNPOD_REST_API_BASE_URL = "https://rest.runpod.io/v1"

_REST_GPU_TYPE_VALUES = tuple(item.value for item in EndpointCreateInputGpuTypeIdsItem)
_REST_GPU_TYPE_BY_NORMALIZED_VALUE = {
    " ".join(value.split()): value for value in _REST_GPU_TYPE_VALUES
}
_REST_GPU_POOL_TO_GPU_TYPES = {
    "AMPERE_16": (
        "NVIDIA RTX A4000",
        "NVIDIA RTX A4500",
        "NVIDIA RTX 4000 Ada Generation",
        "NVIDIA RTX 2000 Ada Generation",
    ),
    "AMPERE_24": (
        "NVIDIA L4",
        "NVIDIA RTX A5000",
        "NVIDIA GeForce RTX 3090",
    ),
    "ADA_24": ("NVIDIA GeForce RTX 4090",),
    "AMPERE_48": (
        "NVIDIA RTX A6000",
        "NVIDIA A40",
    ),
    "ADA_48_PRO": (
        "NVIDIA L40",
        "NVIDIA L40S",
        "NVIDIA RTX 6000 Ada Generation",
    ),
    "AMPERE_80": (
        "NVIDIA A100 80GB PCIe",
        "NVIDIA A100-SXM4-80GB",
    ),
    "ADA_80_PRO": (
        "NVIDIA H100 80GB HBM3",
        "NVIDIA H100 PCIe",
    ),
    "HOPPER_141": (
        "NVIDIA H200",
        "NVIDIA H200 NVL",
    ),
    "ADA_32_PRO": ("NVIDIA RTX 5000 Ada Generation",),
    "BLACKWELL_96": (
        "NVIDIA RTX PRO 6000 Blackwell Server Edition",
        "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
        "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition",
    ),
    "BLACKWELL_180": ("NVIDIA B200",),
}


def _split_csv(value: str | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _canonicalize_gpu_type_id(value: str) -> str:
    normalized = " ".join(value.split())
    canonical = _REST_GPU_TYPE_BY_NORMALIZED_VALUE.get(normalized)
    if canonical:
        return canonical
    raise QuadraError(
        f"Unsupported RunPod gpu_ids value {value!r}. "
        "Use a supported Quadra serverless pool ID or an exact RunPod REST GPU type."
    )


def normalize_gpu_type_ids(gpu_ids: str) -> tuple[str, ...]:
    key = gpu_ids.strip()
    if not key:
        raise QuadraError("runtime.runpod.gpu_ids must not be empty.")
    pool_gpu_types = _REST_GPU_POOL_TO_GPU_TYPES.get(key)
    if pool_gpu_types:
        return tuple(_canonicalize_gpu_type_id(value) for value in pool_gpu_types)

    gpu_type_ids = _split_csv(key)
    if gpu_type_ids:
        return tuple(_canonicalize_gpu_type_id(value) for value in gpu_type_ids)

    raise QuadraError("runtime.runpod.gpu_ids must not be empty.")


def normalize_data_center_ids(locations: str | None) -> tuple[str, ...]:
    return _split_csv(locations)


def execution_timeout_ms(timeout_seconds: int | None) -> int | None:
    if timeout_seconds is None:
        return None
    timeout_ms = max(timeout_seconds, 0) * 1000
    return timeout_ms or None


def build_template_create_body(
    *,
    name: str,
    image_name: str,
    ports: tuple[str, ...],
    docker_entrypoint: tuple[str, ...],
    docker_start_cmd: tuple[str, ...],
    volume_mount_path: str,
    env: dict[str, str],
    container_disk_gb: int,
    readme: str,
) -> TemplateCreateInput:
    payload: dict[str, Any] = {
        "name": name,
        "imageName": image_name,
        "isServerless": True,
        "containerDiskInGb": container_disk_gb,
    }
    if ports:
        payload["ports"] = list(ports)
    if docker_entrypoint:
        payload["dockerEntrypoint"] = list(docker_entrypoint)
    if docker_start_cmd:
        payload["dockerStartCmd"] = list(docker_start_cmd)
    if volume_mount_path:
        payload["volumeMountPath"] = volume_mount_path
    if env:
        payload["env"] = env
    if readme:
        payload["readme"] = readme
    return TemplateCreateInput.from_dict(payload)


def build_template_update_body(
    *,
    name: str,
    image_name: str,
    ports: tuple[str, ...],
    docker_entrypoint: tuple[str, ...],
    docker_start_cmd: tuple[str, ...],
    volume_mount_path: str,
    env: dict[str, str],
    container_disk_gb: int,
    readme: str,
) -> TemplateUpdateInput:
    payload: dict[str, Any] = {
        "name": name,
        "imageName": image_name,
        "containerDiskInGb": container_disk_gb,
    }
    payload["ports"] = list(ports)
    payload["dockerEntrypoint"] = list(docker_entrypoint)
    payload["dockerStartCmd"] = list(docker_start_cmd)
    payload["volumeMountPath"] = volume_mount_path
    payload["env"] = env
    payload["readme"] = readme
    return TemplateUpdateInput.from_dict(payload)


def build_network_volume_create_body(
    *, name: str, data_center_id: str, size_gb: int
) -> NetworkVolumeCreateInput:
    normalized_name = name.strip()
    if not normalized_name:
        raise QuadraError("RunPod network volume name must not be empty.")
    normalized_data_center_id = data_center_id.strip()
    if not normalized_data_center_id:
        raise QuadraError("RunPod network volume datacenter must not be empty.")
    if size_gb <= 0:
        raise QuadraError("RunPod network volume size must be greater than 0 GB.")
    return NetworkVolumeCreateInput(
        data_center_id=normalized_data_center_id,
        name=normalized_name,
        size=size_gb,
    )


def build_endpoint_create_body(
    *,
    name: str,
    template_id: str,
    gpu_ids: str,
    network_volume_id: str,
    locations: str | None,
    idle_timeout: int,
    scaler_type: str,
    scaler_value: int,
    workers_min: int,
    workers_max: int,
    flashboot: bool,
    allowed_cuda_versions: tuple[str, ...],
    gpu_count: int,
    timeout_seconds: int,
) -> EndpointCreateInput:
    payload: dict[str, Any] = {
        "name": name,
        "templateId": template_id,
        "gpuTypeIds": list(normalize_gpu_type_ids(gpu_ids)),
        "networkVolumeId": network_volume_id,
        "idleTimeout": idle_timeout,
        "scalerType": scaler_type,
        "scalerValue": scaler_value,
        "workersMin": workers_min,
        "workersMax": workers_max,
        "flashboot": flashboot,
        "gpuCount": gpu_count,
    }
    data_center_ids = normalize_data_center_ids(locations)
    if data_center_ids:
        payload["dataCenterIds"] = list(data_center_ids)
    if allowed_cuda_versions:
        payload["allowedCudaVersions"] = list(allowed_cuda_versions)
    timeout_ms = execution_timeout_ms(timeout_seconds)
    if timeout_ms is not None:
        payload["executionTimeoutMs"] = timeout_ms
    try:
        return EndpointCreateInput.from_dict(payload)
    except ValueError as exc:
        raise QuadraError(f"Invalid RunPod endpoint configuration: {exc}") from exc


def build_endpoint_update_body(
    *,
    name: str | None = None,
    template_id: str | None = None,
    gpu_ids: str | None = None,
    network_volume_id: str | None = None,
    locations: str | None = None,
    idle_timeout: int | None = None,
    scaler_type: str | None = None,
    scaler_value: int | None = None,
    workers_min: int | None = None,
    workers_max: int | None = None,
    flashboot: bool | None = None,
    allowed_cuda_versions: tuple[str, ...] | None = None,
    gpu_count: int | None = None,
    timeout_seconds: int | None = None,
    rest_payload: dict[str, Any] | None = None,
) -> EndpointUpdateInput:
    payload = dict(rest_payload or {})
    if name is not None:
        payload["name"] = name
    if template_id is not None:
        payload["templateId"] = template_id
    if gpu_ids is not None:
        payload["gpuTypeIds"] = list(normalize_gpu_type_ids(gpu_ids))
    if network_volume_id is not None:
        payload["networkVolumeId"] = network_volume_id
    if locations is not None:
        data_center_ids = normalize_data_center_ids(locations)
        payload["dataCenterIds"] = list(data_center_ids)
    if idle_timeout is not None:
        payload["idleTimeout"] = idle_timeout
    if scaler_type is not None:
        payload["scalerType"] = scaler_type
    if scaler_value is not None:
        payload["scalerValue"] = scaler_value
    if workers_min is not None:
        payload["workersMin"] = workers_min
    if workers_max is not None:
        payload["workersMax"] = workers_max
    if flashboot is not None:
        payload["flashboot"] = flashboot
    if allowed_cuda_versions is not None:
        if allowed_cuda_versions:
            payload["allowedCudaVersions"] = list(allowed_cuda_versions)
        else:
            payload.pop("allowedCudaVersions", None)
    if gpu_count is not None:
        payload["gpuCount"] = gpu_count
    if timeout_seconds is not None:
        timeout_ms = execution_timeout_ms(timeout_seconds)
        payload["executionTimeoutMs"] = 0 if timeout_ms is None else timeout_ms
    if not payload:
        raise QuadraError("At least one RunPod endpoint field must be provided.")
    try:
        return EndpointUpdateInput.from_dict(payload)
    except ValueError as exc:
        raise QuadraError(f"Invalid RunPod endpoint update configuration: {exc}") from exc


def _response_error_message(response: Response[Any]) -> str:
    if not response.content:
        return f"HTTP {response.status_code}"
    text = response.content.decode("utf-8", errors="replace").strip()
    if not text:
        return f"HTTP {response.status_code}"
    try:
        payload = json.loads(text)
    except ValueError:
        return text
    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return text


def _parse_unexpected_success(
    *,
    status_code: int,
    content: bytes,
    success_parser: Callable[[Any], Any] | None,
    invalid_response_message: str,
) -> Any | None:
    if success_parser is None:
        return None
    if status_code < HTTPStatus.OK or status_code >= HTTPStatus.MULTIPLE_CHOICES:
        return None
    try:
        payload = json.loads(content.decode("utf-8", errors="replace"))
    except ValueError as exc:
        raise QuadraError("RunPod returned an invalid JSON response.") from exc
    try:
        return success_parser(payload)
    except (TypeError, ValueError, KeyError) as exc:
        raise QuadraError(invalid_response_message) from exc


class RunpodRestClient:
    def __init__(self, api_key: str):
        self._client = AuthenticatedClient(
            base_url=os.getenv(
                "RUNPOD_REST_API_BASE_URL", DEFAULT_RUNPOD_REST_API_BASE_URL
            ),
            token=api_key,
            headers={"User-Agent": f"Quadra/{__version__}"},
            timeout=httpx.Timeout(30.0),
            raise_on_unexpected_status=True,
        )

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        client = self._client.get_httpx_client()
        try:
            response = client.request(method, path, params=params)
        except httpx.TimeoutException as exc:
            raise QuadraError(f"RunPod request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuadraError(f"RunPod request failed: {exc}") from exc

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise QuadraError("Unauthorized request, please check your RunPod API key.")
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise QuadraError(
                f"RunPod returned HTTP {response.status_code}: "
                f"{_response_error_message(response)}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise QuadraError("RunPod returned an invalid JSON response.") from exc

    def _request(
        self,
        fn: Callable[..., Response[Any]],
        *,
        invalid_response_message: str,
        unexpected_success_parser: Callable[[Any], Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        try:
            response = fn(client=self._client, **kwargs)
        except UnexpectedStatus as exc:
            if exc.status_code == HTTPStatus.UNAUTHORIZED:
                raise QuadraError(
                    "Unauthorized request, please check your RunPod API key."
                ) from exc
            parsed = _parse_unexpected_success(
                status_code=exc.status_code,
                content=exc.content,
                success_parser=unexpected_success_parser,
                invalid_response_message=invalid_response_message,
            )
            if parsed is not None:
                return parsed
            message = exc.content.decode("utf-8", errors="replace").strip()
            raise QuadraError(
                f"RunPod returned HTTP {exc.status_code}: {message or exc.status_code}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise QuadraError(f"RunPod request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuadraError(f"RunPod request failed: {exc}") from exc
        except ValueError as exc:
            raise QuadraError("RunPod returned an invalid JSON response.") from exc

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise QuadraError("Unauthorized request, please check your RunPod API key.")
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise QuadraError(
                f"RunPod returned HTTP {response.status_code}: "
                f"{_response_error_message(response)}"
            )
        if response.parsed is None:
            raise QuadraError(invalid_response_message)
        return response.parsed

    def get_network_volumes(self) -> list[dict[str, Any]]:
        payload = self._request(
            list_network_volumes_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid network volume list response.",
        )
        if not isinstance(payload, list):
            raise QuadraError("RunPod returned an invalid network volume list response.")
        return [item.to_dict() for item in payload if isinstance(item, NetworkVolumesItem)]

    def create_network_volume(
        self, *, name: str, data_center_id: str, size_gb: int
    ) -> dict[str, Any]:
        payload = self._request(
            create_network_volume_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid network volume create response.",
            unexpected_success_parser=NetworkVolume.from_dict,
            body=build_network_volume_create_body(
                name=name,
                data_center_id=data_center_id,
                size_gb=size_gb,
            ),
        )
        return payload.to_dict()

    def get_templates(self) -> list[dict[str, Any]]:
        payload = self._request(
            list_templates_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid template list response.",
        )
        if not isinstance(payload, list):
            raise QuadraError("RunPod returned an invalid template list response.")
        return [item.to_dict() for item in payload]

    def get_template(self, template_id: str) -> dict[str, Any]:
        payload = self._request(
            get_template_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid template response.",
            template_id=template_id,
        )
        return payload.to_dict()

    def create_template(
        self,
        *,
        name: str,
        image_name: str,
        ports: tuple[str, ...],
        docker_entrypoint: tuple[str, ...],
        docker_start_cmd: tuple[str, ...],
        volume_mount_path: str,
        env: dict[str, str],
        container_disk_gb: int,
        readme: str,
    ) -> dict[str, Any]:
        payload = self._request(
            create_template_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid template create response.",
            unexpected_success_parser=Template.from_dict,
            body=build_template_create_body(
                name=name,
                image_name=image_name,
                ports=ports,
                docker_entrypoint=docker_entrypoint,
                docker_start_cmd=docker_start_cmd,
                volume_mount_path=volume_mount_path,
                env=env,
                container_disk_gb=container_disk_gb,
                readme=readme,
            ),
        )
        return payload.to_dict()

    def update_template(
        self,
        template_id: str,
        *,
        name: str,
        image_name: str,
        ports: tuple[str, ...],
        docker_entrypoint: tuple[str, ...],
        docker_start_cmd: tuple[str, ...],
        volume_mount_path: str,
        env: dict[str, str],
        container_disk_gb: int,
        readme: str,
    ) -> dict[str, Any]:
        payload = self._request(
            update_template_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid template update response.",
            template_id=template_id,
            body=build_template_update_body(
                name=name,
                image_name=image_name,
                ports=ports,
                docker_entrypoint=docker_entrypoint,
                docker_start_cmd=docker_start_cmd,
                volume_mount_path=volume_mount_path,
                env=env,
                container_disk_gb=container_disk_gb,
                readme=readme,
            ),
        )
        return payload.to_dict()

    def get_endpoints(self) -> list[dict[str, Any]]:
        payload = self._request_json("GET", "/endpoints")
        if not isinstance(payload, list):
            raise QuadraError("RunPod returned an invalid endpoint list response.")
        return [item for item in payload if isinstance(item, dict)]

    def get_endpoint(
        self, endpoint_id: str, *, include_workers: bool = False
    ) -> dict[str, Any]:
        payload = self._request_json(
            "GET",
            f"/endpoints/{endpoint_id}",
            params={"includeWorkers": include_workers},
        )
        if not isinstance(payload, dict):
            raise QuadraError("RunPod returned an invalid endpoint response.")
        return payload

    def delete_endpoint(self, endpoint_id: str) -> None:
        client = self._client.get_httpx_client()
        try:
            response = client.request("DELETE", f"/endpoints/{endpoint_id}")
        except httpx.TimeoutException as exc:
            raise QuadraError(f"RunPod request timed out: {exc}") from exc
        except httpx.HTTPError as exc:
            raise QuadraError(f"RunPod request failed: {exc}") from exc

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise QuadraError("Unauthorized request, please check your RunPod API key.")
        if response.status_code >= HTTPStatus.BAD_REQUEST:
            raise QuadraError(
                f"RunPod returned HTTP {response.status_code}: "
                f"{_response_error_message(response)}"
            )

    def create_endpoint(
        self,
        *,
        name: str,
        template_id: str,
        gpu_ids: str,
        network_volume_id: str,
        locations: str | None,
        idle_timeout: int,
        scaler_type: str,
        scaler_value: int,
        workers_min: int,
        workers_max: int,
        flashboot: bool,
        allowed_cuda_versions: tuple[str, ...],
        gpu_count: int,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        payload = self._request(
            create_endpoint_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid endpoint create response.",
            unexpected_success_parser=Endpoint.from_dict,
            body=build_endpoint_create_body(
                name=name,
                template_id=template_id,
                gpu_ids=gpu_ids,
                network_volume_id=network_volume_id,
                locations=locations,
                idle_timeout=idle_timeout,
                scaler_type=scaler_type,
                scaler_value=scaler_value,
                workers_min=workers_min,
                workers_max=workers_max,
                flashboot=flashboot,
                allowed_cuda_versions=allowed_cuda_versions,
                gpu_count=gpu_count,
                timeout_seconds=timeout_seconds,
            ),
        )
        return payload.to_dict()

    def update_endpoint(
        self,
        endpoint_id: str,
        rest_payload: dict[str, Any] | None = None,
        *,
        name: str | None = None,
        template_id: str | None = None,
        gpu_ids: str | None = None,
        network_volume_id: str | None = None,
        locations: str | None = None,
        idle_timeout: int | None = None,
        scaler_type: str | None = None,
        scaler_value: int | None = None,
        workers_min: int | None = None,
        workers_max: int | None = None,
        flashboot: bool | None = None,
        allowed_cuda_versions: tuple[str, ...] | None = None,
        gpu_count: int | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        payload = self._request(
            update_endpoint_api.sync_detailed,
            invalid_response_message="RunPod returned an invalid endpoint update response.",
            endpoint_id=endpoint_id,
            body=build_endpoint_update_body(
                name=name,
                template_id=template_id,
                gpu_ids=gpu_ids,
                network_volume_id=network_volume_id,
                locations=locations,
                idle_timeout=idle_timeout,
                scaler_type=scaler_type,
                scaler_value=scaler_value,
                workers_min=workers_min,
                workers_max=workers_max,
                flashboot=flashboot,
                allowed_cuda_versions=allowed_cuda_versions,
                gpu_count=gpu_count,
                timeout_seconds=timeout_seconds,
                rest_payload=rest_payload,
            ),
        )
        return payload.to_dict()
