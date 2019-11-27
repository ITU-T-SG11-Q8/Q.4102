class SingletonInstance:
    _instance = None

    @classmethod
    def _get_instance(cls):
        return cls._instance

    @classmethod
    def get(cls, *args, **kargs):
        cls._instance = cls(*args, **kargs)
        cls.get = cls._get_instance
        return cls._instance
