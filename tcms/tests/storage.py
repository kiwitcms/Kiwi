from collections import OrderedDict

from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles.storage import StaticFilesStorage


def find_files():
    # copied from django.contrib.staticfiles.management.commands.collectstatic
    found_files = OrderedDict()
    for finder in get_finders():
        for path, storage in finder.list([]):
            path = path.replace('\\', '/')
            if path not in found_files:
                found_files[path] = (storage, path)

    return found_files


class RaiseWhenFileNotFound(StaticFilesStorage):
    _files_found = find_files()
    # grappelli uses the following piece of code:
    # window.__admin_media_prefix__ = "{% filter escapejs %}{% static "grappelli/" %}
    # to establish a base URL for all of its assets. This causes this storage class
    # to raise an exception b/c the finder only collects files, not directory names
    _white_list = ["grappelli/"]

    def url(self, name):
        if (name not in self._files_found) and (name not in self._white_list):
            raise Exception('Static file "%s" does not exist and will cause 404 errors!' % name)

        return super().url(name)
