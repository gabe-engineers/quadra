from enum import Enum


class PodCreateInputDataCenterPriority(str, Enum):
    AVAILABILITY = "availability"
    CUSTOM = "custom"

    def __str__(self) -> str:
        return str(self.value)
