from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.endpoint import Endpoint
from ...models.endpoint_update_input import EndpointUpdateInput
from ...types import Response


def _get_kwargs(
    endpoint_id: str,
    *,
    body: EndpointUpdateInput,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/endpoints/{endpoint_id}/update".format(
            endpoint_id=quote(str(endpoint_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Endpoint | None:
    if response.status_code == 200:
        response_200 = Endpoint.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Endpoint]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EndpointUpdateInput,
) -> Response[Any | Endpoint]:
    """Update an endpoint

     Update an endpoint - synonym for PATCH /endpoints/{endpointId}.

    Args:
        endpoint_id (str):
        body (EndpointUpdateInput): Input for updating an endpoint which will trigger a rolling
            release on the endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Endpoint]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EndpointUpdateInput,
) -> Any | Endpoint | None:
    """Update an endpoint

     Update an endpoint - synonym for PATCH /endpoints/{endpointId}.

    Args:
        endpoint_id (str):
        body (EndpointUpdateInput): Input for updating an endpoint which will trigger a rolling
            release on the endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Endpoint
    """

    return sync_detailed(
        endpoint_id=endpoint_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EndpointUpdateInput,
) -> Response[Any | Endpoint]:
    """Update an endpoint

     Update an endpoint - synonym for PATCH /endpoints/{endpointId}.

    Args:
        endpoint_id (str):
        body (EndpointUpdateInput): Input for updating an endpoint which will trigger a rolling
            release on the endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Endpoint]
    """

    kwargs = _get_kwargs(
        endpoint_id=endpoint_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    endpoint_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: EndpointUpdateInput,
) -> Any | Endpoint | None:
    """Update an endpoint

     Update an endpoint - synonym for PATCH /endpoints/{endpointId}.

    Args:
        endpoint_id (str):
        body (EndpointUpdateInput): Input for updating an endpoint which will trigger a rolling
            release on the endpoint.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Endpoint
    """

    return (
        await asyncio_detailed(
            endpoint_id=endpoint_id,
            client=client,
            body=body,
        )
    ).parsed
