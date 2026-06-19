from enum import Enum


class EndpointCreateInputMinCudaVersion(str, Enum):
    VALUE_0 = "13.0"
    VALUE_1 = "12.9"
    VALUE_10 = "12.0"
    VALUE_11 = "11.8"
    VALUE_2 = "12.8"
    VALUE_3 = "12.7"
    VALUE_4 = "12.6"
    VALUE_5 = "12.5"
    VALUE_6 = "12.4"
    VALUE_7 = "12.3"
    VALUE_8 = "12.2"
    VALUE_9 = "12.1"

    def __str__(self) -> str:
        return str(self.value)
