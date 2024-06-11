# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>

# pylint: disable=too-few-public-methods

import markdown


class TestPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self, lines):
        new_lines = []
        test_started = False

        for line in lines:
            if line.lower().find("```test-me") > -1:
                test_started = True
            elif test_started and line.lower().strip() == "```":
                test_started = False

                # inject this instead of the real text
                new_lines.append("Eat, Sleep, Test, Repeat")
            elif test_started:
                # discard current line
                pass
            else:
                new_lines.append(line)

        return new_lines


class TestExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(TestPreprocessor(md), "testing", 35)


def makeExtension(**kwargs):  # pylint: disable=invalid-name
    return TestExtension(**kwargs)
