from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.container_registry_auth import ContainerRegistryAuth
from ...types import Response


def _get_kwargs(
    container_registry_auth_id: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/containerregistryauth/{container_registry_auth_id}".format(
            container_registry_auth_id=quote(str(container_registry_auth_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | ContainerRegistryAuth | None:
    if response.status_code == 200:
        response_200 = ContainerRegistryAuth.from_dict(response.json())

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


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | ContainerRegistryAuth]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    container_registry_auth_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ContainerRegistryAuth]:
    """Find a container registry auth by ID

     Returns a single container registry auth.

    Args:
        container_registry_auth_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ContainerRegistryAuth]
    """

    kwargs = _get_kwargs(
        container_registry_auth_id=container_registry_auth_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    container_registry_auth_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ContainerRegistryAuth | None:
    """Find a container registry auth by ID

     Returns a single container registry auth.

    Args:
        container_registry_auth_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ContainerRegistryAuth
    """

    return sync_detailed(
        container_registry_auth_id=container_registry_auth_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    container_registry_auth_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | ContainerRegistryAuth]:
    """Find a container registry auth by ID

     Returns a single container registry auth.

    Args:
        container_registry_auth_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | ContainerRegistryAuth]
    """

    kwargs = _get_kwargs(
        container_registry_auth_id=container_registry_auth_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    container_registry_auth_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | ContainerRegistryAuth | None:
    """Find a container registry auth by ID

     Returns a single container registry auth.

    Args:
        container_registry_auth_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | ContainerRegistryAuth
    """

    return (
        await asyncio_detailed(
            container_registry_auth_id=container_registry_auth_id,
            client=client,
        )
    ).parsed
