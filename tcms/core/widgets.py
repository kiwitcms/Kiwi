#   Copyright (c) 2018,2021 Kiwi TCMS project. All rights reserved.
#   Author: Alexander Todorov <info@kiwitcms.org>

"""
Custom widgets for Django
"""
from django import forms
from django.utils.dateparse import parse_duration


class SimpleMDE(forms.Textarea):
    """
    SimpleMDE widget for Django
    """

    file_upload_id = "simplemde-file-upload"

    def render(self, name, value, attrs=None, renderer=None):
        # pylint: disable=objects-update-used
        attrs.update(
            {
                "class": "js-simplemde-textarea",
                "data-file-upload-id": self.file_upload_id,
            }
        )
        rendered_string = super().render(name, value, attrs, renderer)
        rendered_string += f"""
<input id="{self.file_upload_id}" type="file" style="display: none">
"""
        return rendered_string

    class Media:
        css = {"all": ["simplemde/dist/simplemde.min.css"]}


class DurationWidget(forms.Widget):
    template_name = "widgets/duration.html"

    def format_value(self, value):
        if not value:
            return 0

        duration = parse_duration(value)
        return int(duration.total_seconds())

    class Media:
        css = {"all": ["bootstrap-duration-picker/dist/bootstrap-duration-picker.css"]}
        js = [
            "bootstrap-duration-picker/dist/bootstrap-duration-picker.js",
        ]
