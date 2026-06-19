import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.billing_records_item import BillingRecordsItem
from ...models.endpoint_billing_bucket_size import EndpointBillingBucketSize
from ...models.endpoint_billing_data_center_id_item import EndpointBillingDataCenterIdItem
from ...models.endpoint_billing_gpu_type_id_item import EndpointBillingGpuTypeIdItem
from ...models.endpoint_billing_grouping import EndpointBillingGrouping
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    bucket_size: EndpointBillingBucketSize | Unset = EndpointBillingBucketSize.DAY,
    data_center_id: list[EndpointBillingDataCenterIdItem] | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    end_time: datetime.datetime | Unset = UNSET,
    gpu_type_id: list[EndpointBillingGpuTypeIdItem] | Unset = UNSET,
    grouping: EndpointBillingGrouping | Unset = EndpointBillingGrouping.ENDPOINTID,
    image_name: str | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_bucket_size: str | Unset = UNSET
    if not isinstance(bucket_size, Unset):
        json_bucket_size = bucket_size.value

    params["bucketSize"] = json_bucket_size

    json_data_center_id: list[str] | Unset = UNSET
    if not isinstance(data_center_id, Unset):
        json_data_center_id = []
        for data_center_id_item_data in data_center_id:
            data_center_id_item = data_center_id_item_data.value
            json_data_center_id.append(data_center_id_item)

    params["dataCenterId"] = json_data_center_id

    params["endpointId"] = endpoint_id

    json_end_time: str | Unset = UNSET
    if not isinstance(end_time, Unset):
        json_end_time = end_time.isoformat()
    params["endTime"] = json_end_time

    json_gpu_type_id: list[str] | Unset = UNSET
    if not isinstance(gpu_type_id, Unset):
        json_gpu_type_id = []
        for gpu_type_id_item_data in gpu_type_id:
            gpu_type_id_item = gpu_type_id_item_data.value
            json_gpu_type_id.append(gpu_type_id_item)

    params["gpuTypeId"] = json_gpu_type_id

    json_grouping: str | Unset = UNSET
    if not isinstance(grouping, Unset):
        json_grouping = grouping.value

    params["grouping"] = json_grouping

    params["imageName"] = image_name

    json_start_time: str | Unset = UNSET
    if not isinstance(start_time, Unset):
        json_start_time = start_time.isoformat()
    params["startTime"] = json_start_time

    params["templateId"] = template_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/billing/endpoints",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> list[BillingRecordsItem] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for componentsschemas_billing_records_item_data in _response_200:
            componentsschemas_billing_records_item = BillingRecordsItem.from_dict(
                componentsschemas_billing_records_item_data
            )

            response_200.append(componentsschemas_billing_records_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[BillingRecordsItem]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: EndpointBillingBucketSize | Unset = EndpointBillingBucketSize.DAY,
    data_center_id: list[EndpointBillingDataCenterIdItem] | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    end_time: datetime.datetime | Unset = UNSET,
    gpu_type_id: list[EndpointBillingGpuTypeIdItem] | Unset = UNSET,
    grouping: EndpointBillingGrouping | Unset = EndpointBillingGrouping.ENDPOINTID,
    image_name: str | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> Response[list[BillingRecordsItem]]:
    """Serverless billing history

     Retrieve billing information about your Serverless endpoints.

    Args:
        bucket_size (EndpointBillingBucketSize | Unset): The length of each billing time bucket.
            The billing time bucket is the time range over which each billing record is aggregated.
            Default: EndpointBillingBucketSize.DAY.
        data_center_id (list[EndpointBillingDataCenterIdItem] | Unset): Filter to endpoints
            located in any of the provided Runpod data centers. The data center IDs are listed in the
            response of the /pods endpoint. Example: ['EU-RO-1', 'CA-MTL-1'].
        endpoint_id (str | Unset): Filter to a specific endpoint. Example: jpnw0v75y3qoql.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        gpu_type_id (list[EndpointBillingGpuTypeIdItem] | Unset): Filter to endpoints with the
            provided GPU type attached. Example: NVIDIA GeForce RTX 4090.
        grouping (EndpointBillingGrouping | Unset): Group the billing records by the provided
            field. Default: EndpointBillingGrouping.ENDPOINTID.
        image_name (str | Unset): Filter to endpoints created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.
        template_id (str | Unset): Filter to endpoints created from the provided template.
            Example: 30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[BillingRecordsItem]]
    """

    kwargs = _get_kwargs(
        bucket_size=bucket_size,
        data_center_id=data_center_id,
        endpoint_id=endpoint_id,
        end_time=end_time,
        gpu_type_id=gpu_type_id,
        grouping=grouping,
        image_name=image_name,
        start_time=start_time,
        template_id=template_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: EndpointBillingBucketSize | Unset = EndpointBillingBucketSize.DAY,
    data_center_id: list[EndpointBillingDataCenterIdItem] | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    end_time: datetime.datetime | Unset = UNSET,
    gpu_type_id: list[EndpointBillingGpuTypeIdItem] | Unset = UNSET,
    grouping: EndpointBillingGrouping | Unset = EndpointBillingGrouping.ENDPOINTID,
    image_name: str | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> list[BillingRecordsItem] | None:
    """Serverless billing history

     Retrieve billing information about your Serverless endpoints.

    Args:
        bucket_size (EndpointBillingBucketSize | Unset): The length of each billing time bucket.
            The billing time bucket is the time range over which each billing record is aggregated.
            Default: EndpointBillingBucketSize.DAY.
        data_center_id (list[EndpointBillingDataCenterIdItem] | Unset): Filter to endpoints
            located in any of the provided Runpod data centers. The data center IDs are listed in the
            response of the /pods endpoint. Example: ['EU-RO-1', 'CA-MTL-1'].
        endpoint_id (str | Unset): Filter to a specific endpoint. Example: jpnw0v75y3qoql.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        gpu_type_id (list[EndpointBillingGpuTypeIdItem] | Unset): Filter to endpoints with the
            provided GPU type attached. Example: NVIDIA GeForce RTX 4090.
        grouping (EndpointBillingGrouping | Unset): Group the billing records by the provided
            field. Default: EndpointBillingGrouping.ENDPOINTID.
        image_name (str | Unset): Filter to endpoints created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.
        template_id (str | Unset): Filter to endpoints created from the provided template.
            Example: 30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[BillingRecordsItem]
    """

    return sync_detailed(
        client=client,
        bucket_size=bucket_size,
        data_center_id=data_center_id,
        endpoint_id=endpoint_id,
        end_time=end_time,
        gpu_type_id=gpu_type_id,
        grouping=grouping,
        image_name=image_name,
        start_time=start_time,
        template_id=template_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: EndpointBillingBucketSize | Unset = EndpointBillingBucketSize.DAY,
    data_center_id: list[EndpointBillingDataCenterIdItem] | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    end_time: datetime.datetime | Unset = UNSET,
    gpu_type_id: list[EndpointBillingGpuTypeIdItem] | Unset = UNSET,
    grouping: EndpointBillingGrouping | Unset = EndpointBillingGrouping.ENDPOINTID,
    image_name: str | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> Response[list[BillingRecordsItem]]:
    """Serverless billing history

     Retrieve billing information about your Serverless endpoints.

    Args:
        bucket_size (EndpointBillingBucketSize | Unset): The length of each billing time bucket.
            The billing time bucket is the time range over which each billing record is aggregated.
            Default: EndpointBillingBucketSize.DAY.
        data_center_id (list[EndpointBillingDataCenterIdItem] | Unset): Filter to endpoints
            located in any of the provided Runpod data centers. The data center IDs are listed in the
            response of the /pods endpoint. Example: ['EU-RO-1', 'CA-MTL-1'].
        endpoint_id (str | Unset): Filter to a specific endpoint. Example: jpnw0v75y3qoql.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        gpu_type_id (list[EndpointBillingGpuTypeIdItem] | Unset): Filter to endpoints with the
            provided GPU type attached. Example: NVIDIA GeForce RTX 4090.
        grouping (EndpointBillingGrouping | Unset): Group the billing records by the provided
            field. Default: EndpointBillingGrouping.ENDPOINTID.
        image_name (str | Unset): Filter to endpoints created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.
        template_id (str | Unset): Filter to endpoints created from the provided template.
            Example: 30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[BillingRecordsItem]]
    """

    kwargs = _get_kwargs(
        bucket_size=bucket_size,
        data_center_id=data_center_id,
        endpoint_id=endpoint_id,
        end_time=end_time,
        gpu_type_id=gpu_type_id,
        grouping=grouping,
        image_name=image_name,
        start_time=start_time,
        template_id=template_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    bucket_size: EndpointBillingBucketSize | Unset = EndpointBillingBucketSize.DAY,
    data_center_id: list[EndpointBillingDataCenterIdItem] | Unset = UNSET,
    endpoint_id: str | Unset = UNSET,
    end_time: datetime.datetime | Unset = UNSET,
    gpu_type_id: list[EndpointBillingGpuTypeIdItem] | Unset = UNSET,
    grouping: EndpointBillingGrouping | Unset = EndpointBillingGrouping.ENDPOINTID,
    image_name: str | Unset = UNSET,
    start_time: datetime.datetime | Unset = UNSET,
    template_id: str | Unset = UNSET,
) -> list[BillingRecordsItem] | None:
    """Serverless billing history

     Retrieve billing information about your Serverless endpoints.

    Args:
        bucket_size (EndpointBillingBucketSize | Unset): The length of each billing time bucket.
            The billing time bucket is the time range over which each billing record is aggregated.
            Default: EndpointBillingBucketSize.DAY.
        data_center_id (list[EndpointBillingDataCenterIdItem] | Unset): Filter to endpoints
            located in any of the provided Runpod data centers. The data center IDs are listed in the
            response of the /pods endpoint. Example: ['EU-RO-1', 'CA-MTL-1'].
        endpoint_id (str | Unset): Filter to a specific endpoint. Example: jpnw0v75y3qoql.
        end_time (datetime.datetime | Unset): The end date of the billing period to retrieve.
            Example: 2023-01-31T23:59:59Z.
        gpu_type_id (list[EndpointBillingGpuTypeIdItem] | Unset): Filter to endpoints with the
            provided GPU type attached. Example: NVIDIA GeForce RTX 4090.
        grouping (EndpointBillingGrouping | Unset): Group the billing records by the provided
            field. Default: EndpointBillingGrouping.ENDPOINTID.
        image_name (str | Unset): Filter to endpoints created with the provided image. Example:
            runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04.
        start_time (datetime.datetime | Unset): The start date of the billing period to retrieve.
            Example: 2023-01-01T00:00:00Z.
        template_id (str | Unset): Filter to endpoints created from the provided template.
            Example: 30zmvf89kd.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[BillingRecordsItem]
    """

    return (
        await asyncio_detailed(
            client=client,
            bucket_size=bucket_size,
            data_center_id=data_center_id,
            endpoint_id=endpoint_id,
            end_time=end_time,
            gpu_type_id=gpu_type_id,
            grouping=grouping,
            image_name=image_name,
            start_time=start_time,
            template_id=template_id,
        )
    ).parsed
