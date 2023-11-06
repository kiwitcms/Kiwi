import os
import re
import string

import astroid
from pylint.checkers import BaseChecker, utils
from textdistance import levenshtein


class SimilarStringChecker(BaseChecker):
    name = "similar-string-checker"

    msgs = {
        "R5011": (
            '"%s" is %.2f%% similar to "%s". Try keeping them the same '
            "to reduce work for translators!",
            "similar-string",
            "Similar strings should be avoided for single translation",
        )
    }

    _dict_of_strings = {}
    threshold = 0.8
    error_messages = []

    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "tcms")
    )

    # NOTE: this works against tcms/ directory and will not take into account
    # if we want to examine only a sub-dir or a few files
    # all files found by os.walk
    all_template_files = set()

    def open(self):
        for rootpath, _dirs, files in os.walk(self.project_root, topdown=False):
            for file_name in files:
                if file_name.endswith((".html", ".txt")):
                    self.all_template_files.add(
                        os.path.join(self.project_root, rootpath, file_name)
                    )

    @staticmethod
    def clean_string(text):
        """
        This method removes the operators and other punctuations
        used in the string to avoid unwanted data to add up to
        the similarity between the strings.
        """
        cleaned = ""
        for char in text:
            if char not in string.punctuation:
                cleaned += char
        return cleaned

    def check_similar_string(self, translation_string):
        cleaned_translation_string = self.clean_string(translation_string)
        for key in self._dict_of_strings:
            similarity = levenshtein.normalized_similarity(
                cleaned_translation_string, self.clean_string(key)
            )
            if similarity >= self.threshold:
                return key, similarity
        return None, None

    @utils.only_required_for_messages("similar-string")
    def visit_call(self, node):
        if not (
            isinstance(node.func, astroid.Name)
            and node.func.name in ("_", "gettext_lazy")
        ):
            return
        if not isinstance(node.args[0], astroid.nodes.Const):
            return

        translation_string = node.args[0].value
        self.check_similar_and_add_error_message(node, translation_string)

    # check if similar string found and add it to error_messages
    def check_similar_and_add_error_message(
        self, node, translation_string, **error_message
    ):
        if translation_string in self._dict_of_strings:
            return

        similar_string, similarity = self.check_similar_string(translation_string)

        if similar_string:
            if isinstance(node, str):
                error_message["node"] = astroid.Module(node, file=node)
            else:
                error_message["node"] = node
            error_message["args"] = (
                translation_string,
                similarity * 100,
                similar_string,
            )
            self.error_messages.append(error_message)
            return
        self._dict_of_strings[translation_string] = True

    # checks each line and find trans or blocktrans tags
    def parse_translation_string(self, filename, lines):
        startline = 0
        startcol = 0
        blocktrans_string = ""

        for lineno, line in enumerate(lines):
            # if pylint disable comment is found ignore and continue with next line
            if re.search(r"<!--\s*pylint\s*:\s*disable\s*-->", line):
                continue

            # if blocktrans starting tag is found
            match_blocktrans_in_line = re.search(r"{% blocktrans[^%}]*%}(.+)", line)
            if match_blocktrans_in_line:
                startline = lineno
                startcol = match_blocktrans_in_line.start(1)
                blocktrans_string = match_blocktrans_in_line.group(1)

            # if line after blocktrans is found
            elif blocktrans_string != "":
                blocktrans_string += line

            # if blocktrans ending tag is found
            endblocktrans_line = re.search(
                r"((.|\n|)*){% endblocktrans %}", blocktrans_string
            )
            if endblocktrans_line:
                blocktrans_string = endblocktrans_line.group(1)
                self.check_similar_and_add_error_message(
                    filename,
                    blocktrans_string,
                    line=startline + 1,
                    col_offset=startcol,
                )
                blocktrans_string = ""

            # if trans tag is found
            # Note: trans tag could be more than one in same
            # line, hence re.finditer rather than re.search)
            match_in_line = re.finditer(r'{% trans "([\w ]+)" %}', line)
            for match in match_in_line:
                translation_string = match.group(1)
                self.check_similar_and_add_error_message(
                    filename,
                    translation_string,
                    line=lineno + 1,
                    col_offset=match.start(1),
                )

    def close(self):
        for filepath in self.all_template_files:
            with open(filepath, "r", encoding="utf-8") as file:
                self.parse_translation_string(filepath, file.readlines())

        for error_message in self.error_messages:
            self.add_message("similar-string", **error_message)
