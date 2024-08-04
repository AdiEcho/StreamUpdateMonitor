from typing import Union
from .netflix import Netflix

Service_T = Union[Netflix]
ServiceMap = {
    "netflix": Netflix,
}

__all__ = ("Netflix", "Service_T", "ServiceMap")

