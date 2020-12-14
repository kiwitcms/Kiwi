from django import forms
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _


class DateTimeField(forms.DateTimeField):
    input_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
    default_error_messages = {
        "invalid": _("Invalid date format. Expected YYYY-MM-DD [HH:MM:SS].")
    }


class UpdateModelFormMixin:  # pylint: disable=too-few-public-methods
    """
    Overrides ModelForm fields so that none of them
    are required. To be used in ModelForms for API .update()
    methods!

    .. warning::

        In multiple inheritance method resolution order matters!
        This needs to be the 1st base class!
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=None,
        empty_permitted=False,
        instance=None,
        use_required_attribute=None,
        renderer=None,
    ):
        super().__init__(
            data,
            files,
            auto_id,
            prefix,
            initial,
            error_class,
            label_suffix,
            empty_permitted,
            instance,
            use_required_attribute,
            renderer,
        )

        for field in self.fields:
            self.fields[field].required = False
            # will cause BaseForm._clean_fields() to reuse the value
            # from self.initial (<-- self.instance) if not specified
            self.fields[field].disabled = field not in data
