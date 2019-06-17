"""function_based_views.py provides a pylint checker FunctionBasedViewChecker that warns
    against using function based views in Django.
"""

from importlib import import_module

import os
import django
from django.conf import settings
from django.urls.resolvers import URLResolver, URLPattern

from pylint import checkers
from pylint import interfaces


class DjangoViewsChecker(checkers.BaseChecker):
    """
    Base class for visiting only astroid modules which contain django views.

    Instance Attributes:
        view_module
        Type :: union[string|None]

            view_module == None,        if the current astroid module does _not_ contain views
            view_module == module.name, if the current astroid module contains _routed_ views

        views_by_module:
        Type :: dict[module_name: str, set[view_name: str]]
    """

    def __init__(self, linter):
        super().__init__(linter)

        if 'DJANGO_SETTINGS_MODULE' in os.environ:
            django.setup()

            project_urls = import_module(settings.ROOT_URLCONF)
            project_urls = project_urls.urlpatterns
        else:
            project_urls = []
        self.views_by_module = self._url_view_mapping(project_urls)
        self.view_module = None

    @classmethod
    def _url_view_mapping(cls, root_urlpatterns):
        def flatten(urlpatterns, prefix='^', result=None):
            """
                Flattens the url graph

                Returns a dictionary of the url pattern string as a key
                and tuple of the module name and the view name
            """

            if result is None:
                result = {None: []}

            for url in urlpatterns:
                if isinstance(url, URLPattern):
                    # path('someurl', view), meaning this is leaf node url
                    result.setdefault(url.callback.__module__, set()).add(url.callback.__name__)
                elif isinstance(url, URLResolver):
                    # path('someurl', include(some_url_patterns)), recurse on some_url_patterns
                    flatten(url.url_patterns,
                            prefix + url.pattern.regex.pattern.strip('^$'),
                            result)

            return result

        return flatten(root_urlpatterns)

    def visit_module(self, node):
        if node.name in self.views_by_module.keys() and not node.name.endswith(".admin"):
            self.view_module = node.name

    def leave_module(self, node):  # pylint: disable=unused-argument
        """
            Reset the current view module b/c otherwise we get false
            reports if a function in another module matches a view name for
            unreset module!
        """
        self.view_module = None


class ClassBasedViewChecker(DjangoViewsChecker):
    """
        This is where we are going to require that all views in
        this project be class based!
    """
    __implements__ = (interfaces.IAstroidChecker, )

    name = 'class-based-view-checker'

    msgs = {
        'R4611': ('Use class based views',
                  'class-based-view-required',
                  'Where possible use generic views. See: '
                  'https://docs.djangoproject.com/en/2.2/topics/class-based-views/generic-display/')
    }

    def visit_functiondef(self, node):
        if node.name in self.views_by_module[self.view_module]:
            self.add_message('class-based-view-required', node=node)
