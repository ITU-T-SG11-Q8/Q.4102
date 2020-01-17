from classes.singleton_instance import SingletonInstance


class Service(SingletonInstance):
    def __init__(self):
        self._overlay_dict = {}
        self._web_socket_message_handler = None

    def get_overlay_dict(self):
        return self._overlay_dict

    def set_overlay(self, key: str, item):
        self._overlay_dict[key] = item

    def get_overlay(self, key: str):
        return self._overlay_dict[key] if key in self._overlay_dict else None

    def delete_overlay(self, key: str):
        del self._overlay_dict[key]

    def get_web_socket_handler(self):
        return self._web_socket_message_handler

    def set_web_socket_handler(self, handler):
        self._web_socket_message_handler = handler
