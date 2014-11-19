# -*- coding: utf-8 -*-
'''
For security purpose, only convert the valid links that ends with .redhat.com.
For the email address, just do the default action.

The redhat_urlize is ported from the core django urlize filter.
'''

import string
from urlparse import urlparse

import re
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeData, mark_safe
from django.utils.encoding import force_unicode
from django.utils.functional import allow_lazy
from django.utils.html import escape
from django.utils.http import urlquote
from django import template


register = template.Library()

LEADING_PUNCTUATION = ['(', '<', '&lt;']
TRAILING_PUNCTUATION = ['.', ',', ')', '>', '\n', '&gt;']

word_split_re = re.compile(r'(\s+)')
simple_email_re = re.compile(r'^\S+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]+$')
punctuation_re = \
    re.compile(
        '^(?P<lead>(?:%s)*)(?P<middle>.*?)(?P<trail>(?:%s)*)$'
        % ('|'.join([re.escape(x) for x in LEADING_PUNCTUATION]),
           '|'.join([re.escape(x) for x in TRAILING_PUNCTUATION])))


def is_redhat_url(url):
    if not url:
        return False
    try:
        from urlparse import ParseResult

        is_compatible_with_py_2_6 = True
    except ImportError:
        is_compatible_with_py_2_6 = False

    parse_result = urlparse(url)
    if is_compatible_with_py_2_6:
        netloc = parse_result.netloc
    else:
        netloc = parse_result[1]

    if netloc:
        return netloc.endswith('redhat.com')
    else:
        return False


def urlize(text, trim_url_limit=None, nofollow=False, autoescape=False):
    """
    Converts any URLs in text into clickable links.

    Works on http://, https://, www. links and links ending in .org, .net or
    .com. Links can have trailing punctuation (periods, commas, close-parens)
    and leading punctuation (opening parens) and it'll still do the right
    thing.

    If trim_url_limit is not None, the URLs in link text longer than this limit
    will truncated to trim_url_limit-3 characters and appended with an elipsis.

    If nofollow is True, the URLs in link text will get a rel="nofollow"
    attribute.

    If autoescape is True, the link text and URLs will get autoescaped.
    """
    trim_url = lambda x, limit=trim_url_limit: limit is not None and (
        len(x) > limit and ('%s...' % x[:max(0, limit - 3)])) or x
    safe_input = isinstance(text, SafeData)
    words = word_split_re.split(force_unicode(text))
    nofollow_attr = nofollow and ' rel="nofollow"' or ''
    for i, word in enumerate(words):
        match = None
        if '.' in word or '@' in word or ':' in word:
            match = punctuation_re.match(word)
        if match:
            lead, middle, trail = match.groups()
            # Make URL we want to point to.
            url = None
            # The URL that ends with redhat.com is valid.
            # Here, only check the web site's URL but the Email address.
            if (middle.startswith('http://') or middle.startswith(
                    'https://')) and is_redhat_url(middle):
                url = urlquote(middle, safe='/&=:;#?+*')
            elif '@' not in middle \
                    and middle \
                    and middle[0] in string.ascii_letters + string.digits \
                    and is_redhat_url(middle):
                url = urlquote('http://%s' % middle, safe='/&=:;#?+*')
            elif '@' in middle \
                    and ':' not in middle \
                    and simple_email_re.match(middle):
                url = 'mailto:%s' % middle
                nofollow_attr = ''
            # Make link.
            if url:
                trimmed = trim_url(middle)
                if autoescape and not safe_input:
                    lead, trail = escape(lead), escape(trail)
                    url, trimmed = escape(url), escape(trimmed)
                middle = '<a href="%s"%s>%s</a>' % \
                         (url, nofollow_attr, trimmed)
                words[i] = mark_safe('%s%s%s' % (lead, middle, trail))
            else:
                if safe_input:
                    words[i] = mark_safe(word)
                elif autoescape:
                    words[i] = escape(word)
        elif safe_input:
            words[i] = mark_safe(word)
        elif autoescape:
            words[i] = escape(word)
    return u''.join(words)


urlize = allow_lazy(urlize, unicode)


@stringfilter
@register.filter
def redhat_urlize(value, classname=''):
    url_pattern = re.compile(
        ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)'
        ur'(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+'
        ur'(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]'
        ur'{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))',
        re.MULTILINE)

    def _replace(match):
        cls = classname and ('class="%s"' % classname) or ''
        href = match.group(0)
        if is_redhat_url(href):
            return '<a href="%s" %s target="_blank">%s</a>' % (href, cls, href)
        else:
            return '<a href="#" %s>%s</a>' % (cls, href)

    if isinstance(value, basestring):
        return mark_safe(url_pattern.sub(_replace, escape(value)))
    else:
        return ''


redhat_urlize.is_safe = True
redhat_urlize.needs_autoescape = True
