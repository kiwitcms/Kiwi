#   Copyright (c) 2018 Kiwi TCMS project. All rights reserved.
#   Author: Alexander Todorov <info@kiwitcms.org>

"""
Custom widgets for Django
"""
from django import forms


class SimpleMDE(forms.Textarea):
    """
        SimpleMDE widget for Django
    """
    def render(self, name, value, attrs=None, renderer=None):
        rendered_string = super().render(name, value, attrs, renderer)
        rendered_string += """
<script>
var simplemde = new SimpleMDE({
    element: document.getElementById("%s"),
    autoDownloadFontAwesome: false,
    renderingConfig: {
        codeSyntaxHighlighting: true,
    },
    toolbar: ["bold", "italic", "heading", "|", "quote",
     "unordered-list", "ordered-list", "|", "link", "image",
     "table", "|", "preview", "side-by-side", "fullscreen", "|", "guide"]
});
</script>
""" % attrs['id']

        return rendered_string

    class Media:
        css = {
            'all': ['simplemde/dist/simplemde.min.css',
                    'prismjs/themes/prism.css']
        }
        js = ['simplemde/dist/simplemde.min.js',
              'marked/marked.min.js',
              'prismjs/prism.js',
              'prismjs/plugins/autoloader/prism-autoloader.min.js',
              'js/simplemde_security_override.js']
