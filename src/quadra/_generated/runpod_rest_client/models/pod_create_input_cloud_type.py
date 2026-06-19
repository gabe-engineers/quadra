from enum import Enum


class PodCreateInputCloudType(str, Enum):
    COMMUNITY = "COMMUNITY"
    SECURE = "SECURE"

    def __str__(self) -> str:
        return str(self.value)
