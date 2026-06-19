from enum import Enum


class PodCreateInputComputeType(str, Enum):
    CPU = "CPU"
    GPU = "GPU"

    def __str__(self) -> str:
        return str(self.value)
