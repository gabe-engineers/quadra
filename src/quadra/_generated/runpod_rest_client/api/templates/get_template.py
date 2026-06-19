from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.template import Template
from ...types import UNSET, Response, Unset


def _get_kwargs(
    template_id: str,
    *,
    include_endpoint_bound_templates: bool | Unset = False,
    include_public_templates: bool | Unset = False,
    include_runpod_templates: bool | Unset = False,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["includeEndpointBoundTemplates"] = include_endpoint_bound_templates

    params["includePublicTemplates"] = include_public_templates

    params["includeRunpodTemplates"] = include_runpod_templates

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/templates/{template_id}".format(
            template_id=quote(str(template_id), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Template | None:
    if response.status_code == 200:
        response_200 = Template.from_dict(response.json())

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


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Template]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_endpoint_bound_templates: bool | Unset = False,
    include_public_templates: bool | Unset = False,
    include_runpod_templates: bool | Unset = False,
) -> Response[Any | Template]:
    """Find a template by ID

     Returns a single template.

    Args:
        template_id (str):
        include_endpoint_bound_templates (bool | Unset): Include templates bound to Serverless
            endpoints in the response. Default: False. Example: True.
        include_public_templates (bool | Unset): Include community-made public templates in the
            response. Default: False. Example: True.
        include_runpod_templates (bool | Unset): Include official Runpod templates in the
            response. Default: False. Example: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Template]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        include_endpoint_bound_templates=include_endpoint_bound_templates,
        include_public_templates=include_public_templates,
        include_runpod_templates=include_runpod_templates,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_endpoint_bound_templates: bool | Unset = False,
    include_public_templates: bool | Unset = False,
    include_runpod_templates: bool | Unset = False,
) -> Any | Template | None:
    """Find a template by ID

     Returns a single template.

    Args:
        template_id (str):
        include_endpoint_bound_templates (bool | Unset): Include templates bound to Serverless
            endpoints in the response. Default: False. Example: True.
        include_public_templates (bool | Unset): Include community-made public templates in the
            response. Default: False. Example: True.
        include_runpod_templates (bool | Unset): Include official Runpod templates in the
            response. Default: False. Example: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Template
    """

    return sync_detailed(
        template_id=template_id,
        client=client,
        include_endpoint_bound_templates=include_endpoint_bound_templates,
        include_public_templates=include_public_templates,
        include_runpod_templates=include_runpod_templates,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_endpoint_bound_templates: bool | Unset = False,
    include_public_templates: bool | Unset = False,
    include_runpod_templates: bool | Unset = False,
) -> Response[Any | Template]:
    """Find a template by ID

     Returns a single template.

    Args:
        template_id (str):
        include_endpoint_bound_templates (bool | Unset): Include templates bound to Serverless
            endpoints in the response. Default: False. Example: True.
        include_public_templates (bool | Unset): Include community-made public templates in the
            response. Default: False. Example: True.
        include_runpod_templates (bool | Unset): Include official Runpod templates in the
            response. Default: False. Example: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Template]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        include_endpoint_bound_templates=include_endpoint_bound_templates,
        include_public_templates=include_public_templates,
        include_runpod_templates=include_runpod_templates,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    include_endpoint_bound_templates: bool | Unset = False,
    include_public_templates: bool | Unset = False,
    include_runpod_templates: bool | Unset = False,
) -> Any | Template | None:
    """Find a template by ID

     Returns a single template.

    Args:
        template_id (str):
        include_endpoint_bound_templates (bool | Unset): Include templates bound to Serverless
            endpoints in the response. Default: False. Example: True.
        include_public_templates (bool | Unset): Include community-made public templates in the
            response. Default: False. Example: True.
        include_runpod_templates (bool | Unset): Include official Runpod templates in the
            response. Default: False. Example: True.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Template
    """

    return (
        await asyncio_detailed(
            template_id=template_id,
            client=client,
            include_endpoint_bound_templates=include_endpoint_bound_templates,
            include_public_templates=include_public_templates,
            include_runpod_templates=include_runpod_templates,
        )
    ).parsed
