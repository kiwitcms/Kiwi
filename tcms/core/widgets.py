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
        rendered_string = super().render(name, value, attrs, renderer)
        rendered_string += """
<input id="%s" type="file" style="display: none">
<script>
$(document).ready(function() {
    initSimpleMDE(document.getElementById('%s'), $('#%s'));
});
</script>
""" % (
            self.file_upload_id,
            attrs["id"],
            self.file_upload_id,
        )

        return rendered_string

    class Media:
        css = {"all": ["simplemde/dist/simplemde.min.css", "prismjs/themes/prism.css"]}
        js = [
            "simplemde/dist/simplemde.min.js",
            "marked/marked.min.js",
            "prismjs/prism.js",
            "prismjs/plugins/autoloader/prism-autoloader.min.js",
            "js/simplemde_security_override.js",
        ]


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
