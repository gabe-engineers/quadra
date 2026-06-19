from enum import Enum


class CudaVersions(str, Enum):
    VALUE_0 = "12.4"
    VALUE_1 = "12.3"
    VALUE_2 = "12.2"
    VALUE_3 = "12.1"
    VALUE_4 = "12.0"
    VALUE_5 = "11.8"

    def __str__(self) -> str:
        return str(self.value)
