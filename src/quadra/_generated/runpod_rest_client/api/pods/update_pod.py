from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.pod import Pod
from ...models.pod_update_input import PodUpdateInput
from ...types import Response


def _get_kwargs(
    pod_id: str,
    *,
    body: PodUpdateInput,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/pods/{pod_id}/update".format(
            pod_id=quote(str(pod_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Pod | None:
    if response.status_code == 200:
        response_200 = Pod.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

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
    body: PodUpdateInput,
) -> Response[Any | Pod]:
    """Update a Pod

     Update a Pod - synonym for PATCH /pods/{podId}.

    Args:
        pod_id (str):
        body (PodUpdateInput): Input for updating a Pod which will trigger a reset.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Pod]
    """

    kwargs = _get_kwargs(
        pod_id=pod_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PodUpdateInput,
) -> Any | Pod | None:
    """Update a Pod

     Update a Pod - synonym for PATCH /pods/{podId}.

    Args:
        pod_id (str):
        body (PodUpdateInput): Input for updating a Pod which will trigger a reset.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Pod
    """

    return sync_detailed(
        pod_id=pod_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PodUpdateInput,
) -> Response[Any | Pod]:
    """Update a Pod

     Update a Pod - synonym for PATCH /pods/{podId}.

    Args:
        pod_id (str):
        body (PodUpdateInput): Input for updating a Pod which will trigger a reset.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Pod]
    """

    kwargs = _get_kwargs(
        pod_id=pod_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    pod_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: PodUpdateInput,
) -> Any | Pod | None:
    """Update a Pod

     Update a Pod - synonym for PATCH /pods/{podId}.

    Args:
        pod_id (str):
        body (PodUpdateInput): Input for updating a Pod which will trigger a reset.

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
            body=body,
        )
    ).parsed
