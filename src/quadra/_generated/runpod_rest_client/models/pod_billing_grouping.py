from enum import Enum


class PodBillingGrouping(str, Enum):
    GPUTYPEID = "gpuTypeId"
    PODID = "podId"

    def __str__(self) -> str:
        return str(self.value)
