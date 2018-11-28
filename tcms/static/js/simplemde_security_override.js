/*
    Override markdown rendering defaults for Simple MDE.

    This resolves XSS vulnerability which can be exploited
    when previewing malicious text in the editor.

    https://github.com/sparksuite/simplemde-markdown-editor/issues/721
    https://snyk.io/vuln/SNYK-JS-SIMPLEMDE-72570
*/

SimpleMDE.prototype._upstream_markdown = SimpleMDE.prototype.markdown;

SimpleMDE.prototype.markdown = function(text) {
    var marked = SimpleMDE.prototype._upstream_markdown();
    marked.setOptions({ sanitize: true });
    return marked;
}
