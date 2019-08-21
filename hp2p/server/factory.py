class Factory:
    _instance = None

    @classmethod
    def _get_instance(cls):
        return cls._instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls._instance = cls(*args, **kargs)
        cls.instance = cls._get_instance
        return cls._instance

    def __init__(self):
        self._dict = {}

    def set_overlay(self, key, item):
        self._dict[key] = item

    def get_overlay(self, key):
        return self._dict[key] if key in self._dict else None

    def delete_overlay(self, key):
        del self._dict[key]
