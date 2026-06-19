from enum import Enum


class EndpointScalerType(str, Enum):
    QUEUE_DELAY = "QUEUE_DELAY"
    REQUEST_COUNT = "REQUEST_COUNT"

    def __str__(self) -> str:
        return str(self.value)
