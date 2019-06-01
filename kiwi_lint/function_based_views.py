"""function_based_views.py provides a pylint checker FunctionBasedViewChecker that warns
    against using function based views in Django.
"""

from importlib import import_module

import django
from django.conf import settings
from django.urls.resolvers import URLResolver, URLPattern

from pylint import checkers
from pylint import interfaces


class DjangoViewsVisiter(checkers.BaseChecker):
    """Base class for visiting only astroid modules which contain django views.

    Instance Attributes:
        view_module
        Type :: union[string|None]

            view_module == None,        if the current astroid module does _not_ contain views
            view_module == module.name, if the current astroid module contains _routed_ views

        url_mapping
        Type :: dict[url_pattern: str, 2-tuple(module_name: str, view_name: str)]

        view_files
        Type :: set[view_file_paths: string]
    """

    def __init__(self, linter):
        super().__init__(linter)

        django.setup()

        project_urls = import_module(settings.ROOT_URLCONF)
        self.url_mapping = self._get_url_view_mapping(project_urls.urlpatterns)
        self.view_files = set(module for module, _ in self.url_mapping.values())
        self.view_module = None

    @classmethod
    def _get_url_view_mapping(cls, root_urlpatterns):
        def go(urlpatterns, prefix='^', result=None):
            """Flattens the url graph

                Returns a dictionary of the url pattern string as a key
                and tuple of the module name and the view name
            """

            if result is None:
                result = {}

            for url in urlpatterns:
                if isinstance(url, URLPattern):
                    # path('someurl', view), meaning this is leaf node url
                    url_pattern = prefix + url.pattern.regex.pattern.strip('^')
                    result[url_pattern] = (url.callback.__module__, url.callback.__name__)

                elif isinstance(url, URLResolver):
                    # path('someurl', include(some_url_patterns)), recurse on some_url_patterns
                    go(url.url_patterns, prefix + url.pattern.regex.pattern.strip('^$'), result)

            return result

        return go(root_urlpatterns)

    def visit_module(self, module):
        self.view_module = module.name if module.name in self.view_files else None


class FunctionBasedViewChecker(DjangoViewsVisiter):
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'django-function-based-view-checker'

    msgs = {'R4611': ('Function based view used, use class based',
                      'non-function-based-view-required',
                      'Function based views are the path to the Dark side!')}

    def __init__(self, linter):
        super().__init__(linter)
        self.views_by_module = self.group_views_by_module(self.url_mapping.values())

    @staticmethod
    def group_views_by_module(module_view_name_pairs):
        by_module = {}
        for module, identifier in module_view_name_pairs:
            by_module.setdefault(module, set()).add(identifier)

        return by_module

    def visit_functiondef(self, func_def):
        if self.view_module and func_def.name in self.views_by_module[self.view_module]:
            self.add_message('non-function-based-view-required', node=func_def)
            print(f'\tview name: \'{func_def.name}\'')
