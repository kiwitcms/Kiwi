"""function_based_views.py provides a pylint checker FunctionBasedViewChecker that warns
    against using function based views in Django.
"""

from collections import OrderedDict
from copy import deepcopy
from importlib import import_module

import astroid

import django
from django.conf import settings
from django.urls.resolvers import URLResolver, URLPattern

from pylint import checkers
from pylint import interfaces


class DjangoViewsVisiter(checkers.BaseChecker):
    """Base class for visiting only astroid modules which contain django views.

    Derivatives could override `visit_views_module` and/or `leave_views_module` to hook just into
    the walking of view containing astroid modules.

    Class Attributes:

    Instance Attributes:
        url_mapping
        Type :: dict[str, 2-tuple(module_name: str, view_name: str)]

        installed_apps_function_filters
        Type :: iterable[callable[all_apps: iterable[str]] -> iterable[str]]

            List of callbacks, which will be called for pruning the installed apps,
            on whose views the checker should be invoked.
    """

    def __init__(self, *args, main_urls_package=None, filters=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.installed_apps_function_filters = filters or []
        django.setup()

        self.__installed_apps = self._get_django_project_apps()
        print(self.__installed_apps)

        project_urls = import_module(main_urls_package)

        self.url_mapping = self._get_url_view_mapping(project_urls.urlpatterns)
        self.url_mapping = self._prune_url_mapping(self.url_mapping, self.__installed_apps)
        self.view_files = set(module for module, _ in self.url_mapping.values())

    def _get_django_project_apps(self):
        installed_apps = deepcopy(settings.INSTALLED_APPS)  # do not mutate the original

        for _filter in self.installed_apps_function_filters:
            # allow void filters that just mutate the list
            res = list(_filter(installed_apps) or [])
            installed_apps = res if res else installed_apps

        return installed_apps

    @classmethod
    def _get_url_view_mapping(cls, urlpatterns, prefix='^', acc=None):
        if acc is None:
            acc = {}

        for url in urlpatterns:
            if isinstance(url, URLPattern):
                key = prefix + url.pattern.regex.pattern.strip('^')
                acc[key] = (url.callback.__module__, url.callback.__name__)

            elif isinstance(url, URLResolver):
                cls._get_url_view_mapping(url.url_patterns, prefix + url.pattern.regex.pattern.strip('^$'), acc)
        return acc

    @staticmethod
    def _prune_url_mapping(url_mapping, installed_apps):
        pruned = url_mapping.__class__()
        for k, (module, name) in url_mapping.items():
            if any(module.startswith(app) for app in installed_apps):
                pruned[k] = (module, name)

        return pruned

    def visit_module(self, module):
        if module.name in self.view_files:
            self.visit_views_module(module)

    def leave_module(self, module):
        if module.name in self.view_files:
            self.leave_views_module(module)

    def visit_views_module(self, module):
        """Called when entering a module with a registered view inside it."""

    def leave_views_module(self, module):
        """Called when leaving from a module with a registered view inside it."""


class FunctionBasedViewChecker(DjangoViewsVisiter):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'django-function-based-view-checker'

    msgs = {'R4611': ('Function based view used, use class based',
                      'non-function-based-view-required',
                      'Function based views are the path to the Dark side!')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.views_by_module = self.group_views_by_module(self.url_mapping.values())

    @staticmethod
    def group_views_by_module(module_view_name_pairs):
        by_module = {}
        for module, identifier in module_view_name_pairs:
            by_module.setdefault(module, set()).add(identifier)

        return by_module

    def visit_views_module(self, module):
        for func_def in module.nodes_of_class(astroid.FunctionDef):
            if func_def.name in self.views_by_module[module.name]:
                self.add_message('non-function-based-view-required', node=func_def)
