/*
    Override markdown rendering defaults for Simple MDE.

    This resolves XSS vulnerability which can be exploited
    when previewing malicious text in the editor.

    https://github.com/sparksuite/simplemde-markdown-editor/issues/721
    https://snyk.io/vuln/SNYK-JS-SIMPLEMDE-72570
*/

SimpleMDE.prototype.markdown = function(text) {
    var markedOptions = { sanitize: true };

    if(this.options && this.options.renderingConfig && this.options.renderingConfig.singleLineBreaks === false) {
        markedOptions.breaks = false;
    } else {
        markedOptions.breaks = true;
    }

    if(this.options && this.options.renderingConfig && this.options.renderingConfig.codeSyntaxHighlighting === true && window.hljs) {
        markedOptions.highlight = function(code) {
            return window.hljs.highlightAuto(code).value;
        };
    }

    marked.setOptions(markedOptions);

    return marked(text);
}
