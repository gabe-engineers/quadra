from enum import Enum


class PodDesiredStatus(str, Enum):
    EXITED = "EXITED"
    RUNNING = "RUNNING"
    TERMINATED = "TERMINATED"

    def __str__(self) -> str:
        return str(self.value)
