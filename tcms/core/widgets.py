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
<input id="simplemde-file-upload" type="file" style="display: none">
<script>
var simplemde = new SimpleMDE({
    element: document.getElementById("%s"),
    autoDownloadFontAwesome: false,
    renderingConfig: {
        codeSyntaxHighlighting: true,
    },
    toolbar: [
        "heading", "bold", "italic", "strikethrough", "|",
        "ordered-list", "unordered-list", "table", "horizontal-rule", "code", "quote", "|",
        "link",
        {
            // todo: standard shortcut is (Ctrl-Alt-I) but I can't find a way
            // to assign shortcuts to customized buttons
            name: "image",
            action: function handler(editor){
                $('#simplemde-file-upload').click();
            },
            className: "fa fa-picture-o",
            title: "Insert Image",
        },
        {
            name: "file",
            action: function handler(editor){
                $('#simplemde-file-upload').click();
            },
            className: "fa fa-paperclip",
            title: "Attach File",
        },
        "|", "preview", "side-by-side", "fullscreen", "|", "guide"
    ],
    autosave: {
        enabled: true,
        uniqueId: window.location.toString(),
        delay: 5000,
    }
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
