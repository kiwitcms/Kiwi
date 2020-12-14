# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.views.generic.base import TemplateView


class Example(TemplateView):  # pylint: disable=missing-permission-required
    template_name = "a_fake_plugin/example.html"
