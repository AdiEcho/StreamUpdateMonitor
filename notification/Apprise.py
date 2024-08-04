from apprise import Apprise
from utils.base_object import Notification, NotificationMSG


class AppriseN(Notification):
    def __init__(self, notification_config):
        super().__init__(notification_config)
        self.apo = Apprise()

    def configuration(self, *args, **kwargs):
        config = kwargs.get("config", {})
        services = config.get("services", [])
        for service in services:
            self.apo.add(service)

    def send_msg(self, msg: NotificationMSG, /, *args, **kwargs):
        return self.apo.notify(
            title=msg.title,
            body=msg.body,
            tag=msg.tag,
        )
