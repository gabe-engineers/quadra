from enum import Enum


class EndpointUpdateInputCpuFlavorIdsItem(str, Enum):
    CPU3C = "cpu3c"
    CPU3G = "cpu3g"
    CPU5C = "cpu5c"
    CPU5G = "cpu5g"

    def __str__(self) -> str:
        return str(self.value)
