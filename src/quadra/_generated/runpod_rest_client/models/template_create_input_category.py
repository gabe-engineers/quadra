from enum import Enum


class TemplateCreateInputCategory(str, Enum):
    AMD = "AMD"
    CPU = "CPU"
    NVIDIA = "NVIDIA"

    def __str__(self) -> str:
        return str(self.value)
