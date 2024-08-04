from .Apprise import AppriseN
from .stdout import STDOutput
from typing import Union

Notification_T = Union[AppriseN]
NotificationMap = {
    "stdout": STDOutput,
    "apprise": AppriseN,
}

__all__ = ["Notification_T", "NotificationMap"]

