# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

import xml.etree.ElementTree as etree  # nosec: B405

import markdown


class StrikeThroughInlineProcessor(markdown.inlinepatterns.InlineProcessor):
    """
    See https://python-markdown.github.io/extensions/api/#example_3
    """

    def handleMatch(self, m, data):
        element = etree.Element("s")
        element.text = m.group(1)
        return element, m.start(0), m.end(0)


class StrikeThroughExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            StrikeThroughInlineProcessor(r"~~(.*?)~~", md), "s", 175
        )


def makeExtension(**kwargs):  # pylint: disable=invalid-name
    return StrikeThroughExtension(**kwargs)
