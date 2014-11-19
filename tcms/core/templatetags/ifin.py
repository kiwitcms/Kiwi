# -*- coding: utf-8 -*-
# Download from http://www.djangosnippets.org/snippets/721/
# All right reserved by  the orignal author(s).
from django.template import Library, TemplateSyntaxError, Node, NodeList, \
    Variable, VariableDoesNotExist

register = Library()


class IfInNode(Node):
    def __init__(self, var1, var2, nodelist_true, nodelist_false, negate):
        self.var1, self.var2 = Variable(var1), Variable(var2)
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.negate = negate

    def __repr__(self):
        return "<IfInNode>"

    def render(self, context):
        try:
            val1 = self.var1.resolve(context)
        except VariableDoesNotExist:
            val1 = None
        try:
            val2 = self.var2.resolve(context)
        except VariableDoesNotExist:
            val2 = None
        try:
            if (self.negate and val1 not in val2) \
                    or (not self.negate and val1 in val2):
                return self.nodelist_true.render(context)
            return self.nodelist_false.render(context)
        except TypeError:
            raise ValueError("Second arg to ifin or ifnotin must be iterable")


def do_ifin(parser, token, negate):
    bits = list(token.split_contents())
    if len(bits) != 3:
        raise TemplateSyntaxError("%r takes two arguments" % bits[0])
    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return IfInNode(bits[1], bits[2], nodelist_true, nodelist_false, negate)


def ifin(parser, token):
    return do_ifin(parser, token, False)


register.tag('ifin', ifin)


def ifnotin(parser, token):
    return do_ifin(parser, token, True)


register.tag('ifnotin', ifnotin)
