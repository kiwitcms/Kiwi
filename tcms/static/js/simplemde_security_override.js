let markdownEditor = undefined

/*
    Override markdown rendering defaults for Simple MDE.

    This resolves XSS vulnerability which can be exploited
    when previewing malicious text in the editor.

    https://github.com/sparksuite/simplemde-markdown-editor/issues/721
    https://snyk.io/vuln/SNYK-JS-SIMPLEMDE-72570
*/
SimpleMDE.prototype.markdown = function (text) {
  alert('RuntimeError - markdown rendering is now backend side')
}

/*
    textArea - a DOM element, not jQuery one, of a text area
    fileUpload - a jQuery element of a hidden file upload field
    autoSaveId - unique ID for autosave!
*/
function initSimpleMDE (textArea, fileUploadElement, autoSaveId = window.location.toString()) {
  if (!textArea || !fileUploadElement) {
    return null
  }

  const simpleMDE = new SimpleMDE({
    element: textArea,
    autoDownloadFontAwesome: false,
    renderingConfig: {
      codeSyntaxHighlighting: true
    },
    toolbar: [
      'heading', 'bold', 'italic', 'strikethrough', '|',
      'ordered-list', 'unordered-list', 'table', 'horizontal-rule', 'code', 'quote', '|',
      'link',
      {
        // todo: standard shortcut is (Ctrl-Alt-I) but I can't find a way
        // to assign shortcuts to customized buttons
        name: 'image',
        action: () => {
          fileUploadElement.click()
        },
        className: 'fa fa-picture-o',
        title: 'Insert Image'
      },
      {
        name: 'file',
        action: () => {
          fileUploadElement.click()
        },
        className: 'fa fa-paperclip',
        title: 'Attach File'
      },
      '|', 'preview', 'side-by-side', 'fullscreen', '|', 'guide'
    ],
    autosave: {
      enabled: true,
      uniqueId: autoSaveId,
      delay: 5000
    },
    tabSize: 4,
    indentWithTabs: false,
    previewRender: function (plainText) {
      let renderedText

      jsonRPC('Markdown.render', plainText, function (result) {
        renderedText = unescapeHTML(result)
      }, true)

      return renderedText
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
        const endPoint = cm.getCursor('end')
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
