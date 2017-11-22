import random

from django.conf import settings
from django.db import connections


class RWRouter(object):
    def __init__(self):
        self.db_list = list(settings.DATABASES.keys())
        self.db_read = list(settings.DATABASES.keys())
        self.db_read.remove('default')

    def db_for_read(self, model, **hints):
        if not self.db_read:
            return self.db_for_write(model, **hints)
        return random.choice(self.db_read)

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the master/slave pool.
        """
        if obj1._state.db in self.db_list and obj2._state.db in self.db_list:
            return True
        return None


class RAWRouter(RWRouter):
    def __init__(self):
        super(RAWRouter, self).__init__()

    def _get_reader(self):
        return connections[self.db_for_read(None)].cursor()

    def _get_writer(self):
        return connections[self.db_for_write(None)].cursor()

    reader_cursor = property(fget=_get_reader)
    writer_cursor = property(fget=_get_writer)


connection = RAWRouter()
