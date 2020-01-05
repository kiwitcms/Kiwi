# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.template.response import TemplateResponse


class ModifySettingsTemplateResponse(TemplateResponse):
    """
        A response class which knows how to modify settings
        while rendering. The attribute ``modify_settings`` must
        be assigned to a :class:`django.test.utils.modify_settings`
        instance before calling ``render()``. For example::

            from django.test.utils import modify_settings

            class MyView(TemplateView):
                ...
                response_class = ModifySettingsTemplateResponse

                def render_to_response(self, context, **response_kwargs):
                    self.response_class.modify_settings = modify_settings(...)
                    return super().render_to_response(context, **response_kwargs)


        .. important::

            The reason we need this class is because when using class
            based views Django supports delayed rendering. Which means
            modifying settings in the view class will not work because
            rendering happens later in the cycle.
    """
    modify_settings = None

    def render(self):
        with self.modify_settings:  # pylint: disable=not-context-manager
            return super().render()
