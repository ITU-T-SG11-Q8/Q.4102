from classes.overlay import Overlay
from classes.singleton_instance import SingletonInstance


class Factory(SingletonInstance):
    def __init__(self):
        self._overlay_dict = {}

    def get_overlay_dict(self):
        return self._overlay_dict

    def set_overlay(self, key: str, item: Overlay):
        self._overlay_dict[key] = item

    def get_overlay(self, key: str):
        return self._overlay_dict[key] if key in self._overlay_dict else None

    def delete_overlay(self, key: str):
        del self._overlay_dict[key]
