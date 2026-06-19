from enum import Enum


class EndpointBillingGrouping(str, Enum):
    ENDPOINTID = "endpointId"
    GPUTYPEID = "gpuTypeId"
    PODID = "podId"

    def __str__(self) -> str:
        return str(self.value)
