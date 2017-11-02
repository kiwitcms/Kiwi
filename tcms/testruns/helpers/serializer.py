# -*- coding: utf-8 -*-
from xml.sax.saxutils import escape


def escape_entities(text):
    '''Convert all XML entities

    @param text: a string containing entities possibly
    @type text: str
    @return: converted version of text
    @rtype: str
    '''
    return escape(text, {'"': '&quot;'}) if text else text
