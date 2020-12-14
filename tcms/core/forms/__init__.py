# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django import forms

from tcms.core.widgets import SimpleMDE


class SimpleCommentForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    """
    A simple class for rendering comment forms which could be
    then manipulated via the JSON-RPC API!
    """

    text = forms.CharField(
        widget=SimpleMDE(),
        required=False,
    )
