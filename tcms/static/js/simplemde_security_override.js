function do_highlight(code, lang) {
    var grammar = window.Prism.languages[lang];
    if (grammar === undefined) {
        // if this is a text with a newly added language the first time we try
        // previewing highlight will fail but load the grammar anyway
        window.Prism.plugins.autoloader.loadLanguages([lang]);
        console.error("Undefined Prism.js grammar for", lang);
        return code;
    }
    return window.Prism.highlight(code, grammar, lang);
};


function parse_and_load_language(textarea) {
    $(textarea).val().split("\n").forEach(function (line) {
        if (line.indexOf("```") === 0) {
            lang = line.trim().split("```")[1];

            if (lang) {
                window.Prism.plugins.autoloader.loadLanguages([lang]);
            }
        }
    });
}

$(document).ready(function () {
    // marked.options.highlight is a synchronous operation *BUT*
    // autoloader.loadLanguages is async and we don't have much control over them
    if (window.Prism && window.Prism.plugins && window.Prism.plugins.autoloader) {
        // parse all textarea's on the page and try to figure out
        // what possible languages are there and load their grammars in advance!
        $.find('textarea').forEach(function (textarea) {
            parse_and_load_language(textarea);
        });

        // keep parsing & trying to load languages as the user types b/c
        // they may be entering new text from scratch
        $('textarea').keyup(function (event) {
            parse_and_load_language($(this));
        });
    }
});


/*
    Override markdown rendering defaults for Simple MDE.

    This resolves XSS vulnerability which can be exploited
    when previewing malicious text in the editor.

    https://github.com/sparksuite/simplemde-markdown-editor/issues/721
    https://snyk.io/vuln/SNYK-JS-SIMPLEMDE-72570
*/
SimpleMDE.prototype.markdown = function (text) {
    var markedOptions = { sanitize: true };

    if (this.options && this.options.renderingConfig && this.options.renderingConfig.singleLineBreaks === false) {
        markedOptions.breaks = false;
    } else {
        markedOptions.breaks = true;
    }

    if (this.options && this.options.renderingConfig && this.options.renderingConfig.codeSyntaxHighlighting === true && window.Prism) {
        markedOptions.highlight = do_highlight;
    }

    marked.setOptions(markedOptions);

    return marked(text);
}

/*
    textArea - a DOM element, not jQuery one, of a text area
    fileUpload - a jQuery element of a hidden file upload field
    autoSaveId - unique ID for autosave!
*/
function initSimpleMDE(textArea, fileUploadElement, autoSaveId=window.location.toString()) {
    if (!textArea || !fileUploadElement) {
        return null;
    }

    const simpleMDE = new SimpleMDE({
        element: textArea,
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
                action: () => {
                    fileUploadElement.click()
                },
                className: "fa fa-picture-o",
                title: "Insert Image",
            },
            {
                name: "file",
                action: () => {
                    fileUploadElement.click()
                },
                className: "fa fa-paperclip",
                title: "Attach File",
            },
            "|", "preview", "side-by-side", "fullscreen", "|", "guide"
        ],
        autosave: {
            enabled: true,
            uniqueId: autoSaveId,
            delay: 5000,
        }
    })

    fileUploadElement.change(function () {
        const attachment = this.files[0]
        const reader = new FileReader()

        reader.onload = e => {
            const dataUri = e.target.result
            const mimeType = dataUri.split(':')[1]
            const b64content = dataUri.split('base64,')[1]

            jsonRPC('User.add_attachment', [attachment.name, b64content], data => {
                const cm = simpleMDE.codemirror
                const endPoint = cm.getCursor("end")
                let text = `[${data.filename}](${data.url})\n`

                if (mimeType.startsWith('image')) {
                    text = '!' + text
                }

                cm.replaceSelection(text)
                endPoint.ch += text.length
                cm.setSelection(endPoint, endPoint)
                cm.focus()
            })
        }
        reader.readAsDataURL(attachment)
    })

    return simpleMDE
}
