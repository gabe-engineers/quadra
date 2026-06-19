from enum import Enum


class PodCreateInputCpuFlavorIdsItem(str, Enum):
    CPU3C = "cpu3c"
    CPU3G = "cpu3g"
    CPU3M = "cpu3m"
    CPU5C = "cpu5c"
    CPU5G = "cpu5g"
    CPU5M = "cpu5m"

    def __str__(self) -> str:
        return str(self.value)
