from enum import Enum


class EndpointComputeType(str, Enum):
    CPU = "CPU"
    GPU = "GPU"

    def __str__(self) -> str:
        return str(self.value)
