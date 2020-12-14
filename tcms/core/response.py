# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.conf import settings
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
        try:
            with self.modify_settings:  # pylint: disable=not-context-manager
                return super().render()
        finally:
            # if this attribute is still set that means disabling settings override
            # failed which leads to navbar showing bogus menu items, see
            # https://github.com/kiwitcms/Kiwi/issues/991
            # => try to restore the original unmodified settings, see
            # django.test.utils.override_settings().disable()
            #
            # NOTE: the only way to reproduce this reliably ATM is by raising exception
            # in .disable() before restoring the original settings although I can see
            # the problem on tcms.kiwitcms.org after the last restart 1 week ago!
            # Maybe the switch to CBV and this response class made #991 harder to
            # reproduce. It was easier to reproduce in the past by triggering some kind
            # of exception in the FBV which used modify_settings() !!!
            if hasattr(self.modify_settings, "wrapped"):
                settings._wrapped = (  # pylint: disable=protected-access
                    self.modify_settings.wrapped
                )
                del self.modify_settings.wrapped
