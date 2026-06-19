from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.template import Template
from ...models.template_update_input import TemplateUpdateInput
from ...types import Response


def _get_kwargs(
    template_id: str,
    *,
    body: TemplateUpdateInput,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/templates/{template_id}/update".format(
            template_id=quote(str(template_id), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Template | None:
    if response.status_code == 200:
        response_200 = Template.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

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
    body: TemplateUpdateInput,
) -> Response[Any | Template]:
    """Update a template

     Update a template - synonym for PATCH /templates/{templateId}.

    Args:
        template_id (str):
        body (TemplateUpdateInput): Input for updating a Template which will trigger a rolling
            release for any associated endpoints.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Template]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TemplateUpdateInput,
) -> Any | Template | None:
    """Update a template

     Update a template - synonym for PATCH /templates/{templateId}.

    Args:
        template_id (str):
        body (TemplateUpdateInput): Input for updating a Template which will trigger a rolling
            release for any associated endpoints.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Template
    """

    return sync_detailed(
        template_id=template_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TemplateUpdateInput,
) -> Response[Any | Template]:
    """Update a template

     Update a template - synonym for PATCH /templates/{templateId}.

    Args:
        template_id (str):
        body (TemplateUpdateInput): Input for updating a Template which will trigger a rolling
            release for any associated endpoints.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Template]
    """

    kwargs = _get_kwargs(
        template_id=template_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    template_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: TemplateUpdateInput,
) -> Any | Template | None:
    """Update a template

     Update a template - synonym for PATCH /templates/{templateId}.

    Args:
        template_id (str):
        body (TemplateUpdateInput): Input for updating a Template which will trigger a rolling
            release for any associated endpoints.

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
            body=body,
        )
    ).parsed
