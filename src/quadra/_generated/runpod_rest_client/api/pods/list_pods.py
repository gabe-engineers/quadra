from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_pods_compute_type import ListPodsComputeType
from ...models.list_pods_desired_status import ListPodsDesiredStatus
from ...models.pod import Pod
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    compute_type: ListPodsComputeType | Unset = UNSET,
    cpu_flavor_id: list[str] | Unset = UNSET,
    data_center_id: list[str] | Unset = UNSET,
    desired_status: ListPodsDesiredStatus | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    gpu_type_id: list[str] | Unset = UNSET,
    id: str | Unset = UNSET,
    image_name: str | Unset = UNSET,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
    name: str | Unset = UNSET,
    network_volume_id: str | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_compute_type: str | Unset = UNSET
    if not isinstance(compute_type, Unset):
        json_compute_type = compute_type.value

    params["computeType"] = json_compute_type

    json_cpu_flavor_id: list[str] | Unset = UNSET
    if not isinstance(cpu_flavor_id, Unset):
        json_cpu_flavor_id = cpu_flavor_id

    params["cpuFlavorId"] = json_cpu_flavor_id

    json_data_center_id: list[str] | Unset = UNSET
    if not isinstance(data_center_id, Unset):
        json_data_center_id = data_center_id

    params["dataCenterId"] = json_data_center_id

    json_desired_status: str | Unset = UNSET
    if not isinstance(desired_status, Unset):
        json_desired_status = desired_status.value

    params["desiredStatus"] = json_desired_status

    params["endpointId"] = endpoint_id

    json_gpu_type_id: list[str] | Unset = UNSET
    if not isinstance(gpu_type_id, Unset):
        json_gpu_type_id = gpu_type_id

    params["gpuTypeId"] = json_gpu_type_id

    params["id"] = id

    params["imageName"] = image_name

    params["includeMachine"] = include_machine

    params["includeNetworkVolume"] = include_network_volume

    params["includeSavingsPlans"] = include_savings_plans

    params["includeTemplate"] = include_template

    params["includeWorkers"] = include_workers

    params["name"] = name

    params["networkVolumeId"] = network_volume_id

    params["templateId"] = template_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/pods",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | list[Pod] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemas_pods_item_data in _response_200:
            componentsschemas_pods_item = Pod.from_dict(componentsschemas_pods_item_data)

            response_200.append(componentsschemas_pods_item)

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 404:
        response_404 = cast(Any, None)
        return response_404

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | list[Pod]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    compute_type: ListPodsComputeType | Unset = UNSET,
    cpu_flavor_id: list[str] | Unset = UNSET,
    data_center_id: list[str] | Unset = UNSET,
    desired_status: ListPodsDesiredStatus | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    gpu_type_id: list[str] | Unset = UNSET,
    id: str | Unset = UNSET,
    image_name: str | Unset = UNSET,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
    name: str | Unset = UNSET,
    network_volume_id: str | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> Response[Any | list[Pod]]:
    """List Pods

     Returns a list of Pods.

    Args:
        compute_type (ListPodsComputeType | Unset): Filter to only GPU or only CPU Pods. Example:
            CPU.
        cpu_flavor_id (list[str] | Unset): Filter to CPU Pods with any of the listed CPU flavors.
            Example: ['cpu3c', 'cpu5g'].
        data_center_id (list[str] | Unset): Filter to Pods located in any of the provided Runpod
            data centers. Example: ['EU-RO-1'].
        desired_status (ListPodsDesiredStatus | Unset): Filter to Pods currently in the provided
            state. Example: RUNNING.
        endpoint_id (str | Unset): Filter to workers on the provided Serverless endpoint (note
            that endpoint workers are not included in the response by default, set includeWorkers to
            true to include them).
        gpu_type_id (list[str] | Unset): Filter to Pods with any of the listed GPU types attached.
            Example: ['NVIDIA GeForce RTX 4090', 'NVIDIA RTX A5000'].
        id (str | Unset): Filter to a specific Pod. Example: xedezhzb9la3ye.
        image_name (str | Unset): Filter to Pods created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        include_machine (bool | Unset): Include information about the machine the Pod is running
            on. Default: False. Example: True.
        include_network_volume (bool | Unset): Include information about the network volume
            attached to the returned Pod, if any. Default: False. Example: True.
        include_savings_plans (bool | Unset): Include information about the savings plans applied
            to the Pod. Default: False. Example: True.
        include_template (bool | Unset): Include information about the template the Pod uses, if
            any. Default: False. Example: True.
        include_workers (bool | Unset): Set to true to also list Pods which are Serverless
            workers. Default: False. Example: True.
        name (str | Unset): Filter to Pods with the provided name.
        network_volume_id (str | Unset): Filter to Pods with the provided network volume attached.
            Example: agv6w2qcg7.
        template_id (str | Unset): Filter to Pods created from the provided template. Example:
            30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | list[Pod]]
    """

    kwargs = _get_kwargs(
        compute_type=compute_type,
        cpu_flavor_id=cpu_flavor_id,
        data_center_id=data_center_id,
        desired_status=desired_status,
        endpoint_id=endpoint_id,
        gpu_type_id=gpu_type_id,
        id=id,
        image_name=image_name,
        include_machine=include_machine,
        include_network_volume=include_network_volume,
        include_savings_plans=include_savings_plans,
        include_template=include_template,
        include_workers=include_workers,
        name=name,
        network_volume_id=network_volume_id,
        template_id=template_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    compute_type: ListPodsComputeType | Unset = UNSET,
    cpu_flavor_id: list[str] | Unset = UNSET,
    data_center_id: list[str] | Unset = UNSET,
    desired_status: ListPodsDesiredStatus | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    gpu_type_id: list[str] | Unset = UNSET,
    id: str | Unset = UNSET,
    image_name: str | Unset = UNSET,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
    name: str | Unset = UNSET,
    network_volume_id: str | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> Any | list[Pod] | None:
    """List Pods

     Returns a list of Pods.

    Args:
        compute_type (ListPodsComputeType | Unset): Filter to only GPU or only CPU Pods. Example:
            CPU.
        cpu_flavor_id (list[str] | Unset): Filter to CPU Pods with any of the listed CPU flavors.
            Example: ['cpu3c', 'cpu5g'].
        data_center_id (list[str] | Unset): Filter to Pods located in any of the provided Runpod
            data centers. Example: ['EU-RO-1'].
        desired_status (ListPodsDesiredStatus | Unset): Filter to Pods currently in the provided
            state. Example: RUNNING.
        endpoint_id (str | Unset): Filter to workers on the provided Serverless endpoint (note
            that endpoint workers are not included in the response by default, set includeWorkers to
            true to include them).
        gpu_type_id (list[str] | Unset): Filter to Pods with any of the listed GPU types attached.
            Example: ['NVIDIA GeForce RTX 4090', 'NVIDIA RTX A5000'].
        id (str | Unset): Filter to a specific Pod. Example: xedezhzb9la3ye.
        image_name (str | Unset): Filter to Pods created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        include_machine (bool | Unset): Include information about the machine the Pod is running
            on. Default: False. Example: True.
        include_network_volume (bool | Unset): Include information about the network volume
            attached to the returned Pod, if any. Default: False. Example: True.
        include_savings_plans (bool | Unset): Include information about the savings plans applied
            to the Pod. Default: False. Example: True.
        include_template (bool | Unset): Include information about the template the Pod uses, if
            any. Default: False. Example: True.
        include_workers (bool | Unset): Set to true to also list Pods which are Serverless
            workers. Default: False. Example: True.
        name (str | Unset): Filter to Pods with the provided name.
        network_volume_id (str | Unset): Filter to Pods with the provided network volume attached.
            Example: agv6w2qcg7.
        template_id (str | Unset): Filter to Pods created from the provided template. Example:
            30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | list[Pod]
    """

    return sync_detailed(
        client=client,
        compute_type=compute_type,
        cpu_flavor_id=cpu_flavor_id,
        data_center_id=data_center_id,
        desired_status=desired_status,
        endpoint_id=endpoint_id,
        gpu_type_id=gpu_type_id,
        id=id,
        image_name=image_name,
        include_machine=include_machine,
        include_network_volume=include_network_volume,
        include_savings_plans=include_savings_plans,
        include_template=include_template,
        include_workers=include_workers,
        name=name,
        network_volume_id=network_volume_id,
        template_id=template_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    compute_type: ListPodsComputeType | Unset = UNSET,
    cpu_flavor_id: list[str] | Unset = UNSET,
    data_center_id: list[str] | Unset = UNSET,
    desired_status: ListPodsDesiredStatus | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    gpu_type_id: list[str] | Unset = UNSET,
    id: str | Unset = UNSET,
    image_name: str | Unset = UNSET,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
    name: str | Unset = UNSET,
    network_volume_id: str | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> Response[Any | list[Pod]]:
    """List Pods

     Returns a list of Pods.

    Args:
        compute_type (ListPodsComputeType | Unset): Filter to only GPU or only CPU Pods. Example:
            CPU.
        cpu_flavor_id (list[str] | Unset): Filter to CPU Pods with any of the listed CPU flavors.
            Example: ['cpu3c', 'cpu5g'].
        data_center_id (list[str] | Unset): Filter to Pods located in any of the provided Runpod
            data centers. Example: ['EU-RO-1'].
        desired_status (ListPodsDesiredStatus | Unset): Filter to Pods currently in the provided
            state. Example: RUNNING.
        endpoint_id (str | Unset): Filter to workers on the provided Serverless endpoint (note
            that endpoint workers are not included in the response by default, set includeWorkers to
            true to include them).
        gpu_type_id (list[str] | Unset): Filter to Pods with any of the listed GPU types attached.
            Example: ['NVIDIA GeForce RTX 4090', 'NVIDIA RTX A5000'].
        id (str | Unset): Filter to a specific Pod. Example: xedezhzb9la3ye.
        image_name (str | Unset): Filter to Pods created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        include_machine (bool | Unset): Include information about the machine the Pod is running
            on. Default: False. Example: True.
        include_network_volume (bool | Unset): Include information about the network volume
            attached to the returned Pod, if any. Default: False. Example: True.
        include_savings_plans (bool | Unset): Include information about the savings plans applied
            to the Pod. Default: False. Example: True.
        include_template (bool | Unset): Include information about the template the Pod uses, if
            any. Default: False. Example: True.
        include_workers (bool | Unset): Set to true to also list Pods which are Serverless
            workers. Default: False. Example: True.
        name (str | Unset): Filter to Pods with the provided name.
        network_volume_id (str | Unset): Filter to Pods with the provided network volume attached.
            Example: agv6w2qcg7.
        template_id (str | Unset): Filter to Pods created from the provided template. Example:
            30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | list[Pod]]
    """

    kwargs = _get_kwargs(
        compute_type=compute_type,
        cpu_flavor_id=cpu_flavor_id,
        data_center_id=data_center_id,
        desired_status=desired_status,
        endpoint_id=endpoint_id,
        gpu_type_id=gpu_type_id,
        id=id,
        image_name=image_name,
        include_machine=include_machine,
        include_network_volume=include_network_volume,
        include_savings_plans=include_savings_plans,
        include_template=include_template,
        include_workers=include_workers,
        name=name,
        network_volume_id=network_volume_id,
        template_id=template_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    compute_type: ListPodsComputeType | Unset = UNSET,
    cpu_flavor_id: list[str] | Unset = UNSET,
    data_center_id: list[str] | Unset = UNSET,
    desired_status: ListPodsDesiredStatus | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    gpu_type_id: list[str] | Unset = UNSET,
    id: str | Unset = UNSET,
    image_name: str | Unset = UNSET,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
    name: str | Unset = UNSET,
    network_volume_id: str | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> Any | list[Pod] | None:
    """List Pods

     Returns a list of Pods.

    Args:
        compute_type (ListPodsComputeType | Unset): Filter to only GPU or only CPU Pods. Example:
            CPU.
        cpu_flavor_id (list[str] | Unset): Filter to CPU Pods with any of the listed CPU flavors.
            Example: ['cpu3c', 'cpu5g'].
        data_center_id (list[str] | Unset): Filter to Pods located in any of the provided Runpod
            data centers. Example: ['EU-RO-1'].
        desired_status (ListPodsDesiredStatus | Unset): Filter to Pods currently in the provided
            state. Example: RUNNING.
        endpoint_id (str | Unset): Filter to workers on the provided Serverless endpoint (note
            that endpoint workers are not included in the response by default, set includeWorkers to
            true to include them).
        gpu_type_id (list[str] | Unset): Filter to Pods with any of the listed GPU types attached.
            Example: ['NVIDIA GeForce RTX 4090', 'NVIDIA RTX A5000'].
        id (str | Unset): Filter to a specific Pod. Example: xedezhzb9la3ye.
        image_name (str | Unset): Filter to Pods created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        include_machine (bool | Unset): Include information about the machine the Pod is running
            on. Default: False. Example: True.
        include_network_volume (bool | Unset): Include information about the network volume
            attached to the returned Pod, if any. Default: False. Example: True.
        include_savings_plans (bool | Unset): Include information about the savings plans applied
            to the Pod. Default: False. Example: True.
        include_template (bool | Unset): Include information about the template the Pod uses, if
            any. Default: False. Example: True.
        include_workers (bool | Unset): Set to true to also list Pods which are Serverless
            workers. Default: False. Example: True.
        name (str | Unset): Filter to Pods with the provided name.
        network_volume_id (str | Unset): Filter to Pods with the provided network volume attached.
            Example: agv6w2qcg7.
        template_id (str | Unset): Filter to Pods created from the provided template. Example:
            30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | list[Pod]
    """

    return (
        await asyncio_detailed(
            client=client,
            compute_type=compute_type,
            cpu_flavor_id=cpu_flavor_id,
            data_center_id=data_center_id,
            desired_status=desired_status,
            endpoint_id=endpoint_id,
            gpu_type_id=gpu_type_id,
            id=id,
            image_name=image_name,
            include_machine=include_machine,
            include_network_volume=include_network_volume,
            include_savings_plans=include_savings_plans,
            include_template=include_template,
            include_workers=include_workers,
            name=name,
            network_volume_id=network_volume_id,
            template_id=template_id,
        )
    ).parsed
