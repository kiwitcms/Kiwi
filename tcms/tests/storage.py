from collections import OrderedDict

from django.contrib.staticfiles.storage import StaticFilesStorage
from django.contrib.staticfiles.finders import get_finders


def find_files():
    # copied from django.contrib.staticfiles.management.commands.collectstatic
    found_files = OrderedDict()
    for finder in get_finders():
        for path, storage in finder.list([]):
            if path not in found_files:
                found_files[path] = (storage, path)

    return found_files


class RaiseWhenFileNotFound(StaticFilesStorage):
    _files_found = find_files()

    def url(self, name):
        if name not in self._files_found:
            raise Exception('Static file "%s" does not exist and will cause 404 errors!' % name)

        return super(RaiseWhenFileNotFound, self).url(name)
