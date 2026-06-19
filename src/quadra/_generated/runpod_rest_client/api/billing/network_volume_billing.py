import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.network_volume_billing_bucket_size import NetworkVolumeBillingBucketSize
from ...models.network_volume_billing_records_item import NetworkVolumeBillingRecordsItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    bucket_size: NetworkVolumeBillingBucketSize | Unset = NetworkVolumeBillingBucketSize.DAY,
    end_time: datetime.datetime | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_bucket_size: str | Unset = UNSET
    if not isinstance(bucket_size, Unset):
        json_bucket_size = bucket_size.value

    params["bucketSize"] = json_bucket_size

    json_end_time: str | Unset = UNSET
    if not isinstance(end_time, Unset):
        json_end_time = end_time.isoformat()
    params["endTime"] = json_end_time

    json_start_time: str | Unset = UNSET
    if not isinstance(start_time, Unset):
        json_start_time = start_time.isoformat()
    params["startTime"] = json_start_time

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/billing/networkvolumes",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> list[NetworkVolumeBillingRecordsItem] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemas_network_volume_billing_records_item_data in _response_200:
            componentsschemas_network_volume_billing_records_item = NetworkVolumeBillingRecordsItem.from_dict(
                componentsschemas_network_volume_billing_records_item_data
            )

            response_200.append(componentsschemas_network_volume_billing_records_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[NetworkVolumeBillingRecordsItem]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: NetworkVolumeBillingBucketSize | Unset = NetworkVolumeBillingBucketSize.DAY,
    end_time: datetime.datetime | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
) -> Response[list[NetworkVolumeBillingRecordsItem]]:
    """Network volume billing history

     Retrieve billing information about your network volumes.

    Args:
        bucket_size (NetworkVolumeBillingBucketSize | Unset): The length of each billing time
            bucket. The billing time bucket is the time range over which each billing record is
            aggregated. Default: NetworkVolumeBillingBucketSize.DAY.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[NetworkVolumeBillingRecordsItem]]
    """

    kwargs = _get_kwargs(
        bucket_size=bucket_size,
        end_time=end_time,
        start_time=start_time,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: NetworkVolumeBillingBucketSize | Unset = NetworkVolumeBillingBucketSize.DAY,
    end_time: datetime.datetime | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
) -> list[NetworkVolumeBillingRecordsItem] | None:
    """Network volume billing history

     Retrieve billing information about your network volumes.

    Args:
        bucket_size (NetworkVolumeBillingBucketSize | Unset): The length of each billing time
            bucket. The billing time bucket is the time range over which each billing record is
            aggregated. Default: NetworkVolumeBillingBucketSize.DAY.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[NetworkVolumeBillingRecordsItem]
    """

    return sync_detailed(
        client=client,
        bucket_size=bucket_size,
        end_time=end_time,
        start_time=start_time,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: NetworkVolumeBillingBucketSize | Unset = NetworkVolumeBillingBucketSize.DAY,
    end_time: datetime.datetime | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
) -> Response[list[NetworkVolumeBillingRecordsItem]]:
    """Network volume billing history

     Retrieve billing information about your network volumes.

    Args:
        bucket_size (NetworkVolumeBillingBucketSize | Unset): The length of each billing time
            bucket. The billing time bucket is the time range over which each billing record is
            aggregated. Default: NetworkVolumeBillingBucketSize.DAY.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[NetworkVolumeBillingRecordsItem]]
    """

    kwargs = _get_kwargs(
        bucket_size=bucket_size,
        end_time=end_time,
        start_time=start_time,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: NetworkVolumeBillingBucketSize | Unset = NetworkVolumeBillingBucketSize.DAY,
    end_time: datetime.datetime | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
) -> list[NetworkVolumeBillingRecordsItem] | None:
    """Network volume billing history

     Retrieve billing information about your network volumes.

    Args:
        bucket_size (NetworkVolumeBillingBucketSize | Unset): The length of each billing time
            bucket. The billing time bucket is the time range over which each billing record is
            aggregated. Default: NetworkVolumeBillingBucketSize.DAY.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[NetworkVolumeBillingRecordsItem]
    """

    return (
        await asyncio_detailed(
            client=client,
            bucket_size=bucket_size,
            end_time=end_time,
            start_time=start_time,
        )
    ).parsed
