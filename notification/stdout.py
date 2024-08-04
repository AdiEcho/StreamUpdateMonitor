from utils.base_object import Notification, NotificationMSG


class STDOutput(Notification):
    def __init__(self, notification_config: dict):
        super().__init__(notification_config)
        ...

    def configuration(self, *args, **kwargs):
        ...

    @staticmethod
    def send_msg(msg: NotificationMSG, /, *args, **kwargs):
        print(f"{msg.title}\n{msg.body}")
        return True
