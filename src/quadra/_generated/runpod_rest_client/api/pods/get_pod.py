from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.pod import Pod
from ...types import UNSET, Response, Unset


def _get_kwargs(
    pod_id: str,
    *,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["includeMachine"] = include_machine

    params["includeNetworkVolume"] = include_network_volume

    params["includeSavingsPlans"] = include_savings_plans

    params["includeTemplate"] = include_template

    params["includeWorkers"] = include_workers

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/pods/{pod_id}".format(
            pod_id=quote(str(pod_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Pod | None:
    if response.status_code == 200:
        response_200 = Pod.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Pod]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
) -> Response[Any | Pod]:
    """Find a Pod by ID

     Returns a single Pod.

    Args:
        pod_id (str):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Pod]
    """

    kwargs = _get_kwargs(
        pod_id=pod_id,
        include_machine=include_machine,
        include_network_volume=include_network_volume,
        include_savings_plans=include_savings_plans,
        include_template=include_template,
        include_workers=include_workers,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
) -> Any | Pod | None:
    """Find a Pod by ID

     Returns a single Pod.

    Args:
        pod_id (str):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Pod
    """

    return sync_detailed(
        pod_id=pod_id,
        client=client,
        include_machine=include_machine,
        include_network_volume=include_network_volume,
        include_savings_plans=include_savings_plans,
        include_template=include_template,
        include_workers=include_workers,
    ).parsed


async def asyncio_detailed(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
) -> Response[Any | Pod]:
    """Find a Pod by ID

     Returns a single Pod.

    Args:
        pod_id (str):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Pod]
    """

    kwargs = _get_kwargs(
        pod_id=pod_id,
        include_machine=include_machine,
        include_network_volume=include_network_volume,
        include_savings_plans=include_savings_plans,
        include_template=include_template,
        include_workers=include_workers,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_machine: bool | Unset = False,
    include_network_volume: bool | Unset = False,
    include_savings_plans: bool | Unset = False,
    include_template: bool | Unset = False,
    include_workers: bool | Unset = False,
) -> Any | Pod | None:
    """Find a Pod by ID

     Returns a single Pod.

    Args:
        pod_id (str):
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

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Pod
    """

    return (
        await asyncio_detailed(
            pod_id=pod_id,
            client=client,
            include_machine=include_machine,
            include_network_volume=include_network_volume,
            include_savings_plans=include_savings_plans,
            include_template=include_template,
            include_workers=include_workers,
        )
    ).parsed
