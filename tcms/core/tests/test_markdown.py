# -*- coding: utf-8 -*-
import unittest
from tcms.core.templatetags.extra_filters import markdown2html


class TestMarkdownExtraFilters(unittest.TestCase):

    def test_markdown2html_convert_paragraphs(self):
        self.assertEqual(markdown2html("__*hello!*__"),
                         "<p><strong><em>hello!</em></strong></p>")

    def test_markdown2html_convert_tables(self):
        self.assertEqual(markdown2html("""|Stx |Desc |\n|----|-----|\n|Head|Title|\n|Txt|Txt |"""),
                         """<table>
<thead>
<tr>
<th>Stx</th>
<th>Desc</th>
</tr>
</thead>
<tbody>
<tr>
<td>Head</td>
<td>Title</td>
</tr>
<tr>
<td>Txt</td>
<td>Txt</td>
</tr>
</tbody>
</table>""")

    def test_markdown2html_convert_nl2br(self):
        self.assertEqual(markdown2html("""Line 1
Line 2"""), """<p>Line 1<br>
Line 2</p>""")

    def test_markdown2html_convert_fenced_code(self):
        self.assertEqual(markdown2html("""```{
"firstName": "John",
"lastName": "Smith",
"age": 25}``` """), """<p><code>{
"firstName": "John",
"lastName": "Smith",
"age": 25}</code> </p>""")

    def test_markdown2html_with_codehilite(self):
        self.assertEqual(markdown2html("""```python
def hello():
    pass
```"""), """<div class="python codehilite"><pre><span></span>\
<code><span class="k">def</span> <span class="nf">hello</span><span class="p">():</span>
    <span class="k">pass</span>
</code></pre></div>""")

    def test_markdown2html_does_bleach_unsafe_code(self):
        self.assertEqual(markdown2html("### hello <script>alert('gotcha');</script>"),
                         "<h3>hello &lt;script&gt;alert('gotcha');&lt;/script&gt;</h3>")

        self.assertEqual(markdown2html("<canvas><bgsound><audio><applet>"),
                         "&lt;canvas&gt;&lt;bgsound&gt;&lt;audio&gt;&lt;applet&gt;")

        self.assertEqual(markdown2html("""_hello_ <html><head></head>
<body></body></html>"""), """<p><em>hello</em> &lt;html&gt;&lt;head&gt;&lt;/head&gt;<br>
&lt;body&gt;&lt;/body&gt;&lt;/html&gt;</p>""")

        self.assertEqual(markdown2html("""__hello__ <xmp><video><track>
<title><rt><ruby><param>"""), """<p><strong>hello</strong> &lt;xmp&gt;&lt;video&gt;&lt;track&gt;<br>
&lt;title&gt;&lt;rt&gt;&lt;ruby&gt;&lt;param&gt;</p>""")

        self.assertEqual(markdown2html("""*hello* <object><link><iframe>
<frame><frameset><embed>"""), """<p><em>hello</em> &lt;object&gt;&lt;link&gt;&lt;iframe&gt;<br>
&lt;frame&gt;&lt;frameset&gt;&lt;embed&gt;</p>""")
