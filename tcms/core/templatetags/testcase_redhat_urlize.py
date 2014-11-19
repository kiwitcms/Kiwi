# -*- coding: utf-8 -*-

# TODO: replace the variable name 'domain_name' with a more descriptive one.

import unittest

from tcms.core.templatetags.redhat_urlize import redhat_urlize


class Test_redhat_urlize(unittest.TestCase):
    ''' Testing the custom redhat_urlize filter '''

    def test_only_domain_ends_with_redhat_com(self):
        domain_name = 'www.redhat.com'
        result = redhat_urlize(domain_name)
        expected = '<a href="http://www.redhat.com" ' \
                   'rel="nofollow">www.redhat.com</a>'
        self.assertEqual(result, expected)

        domain_name = 'http://home.corp.redhat.com'
        result = redhat_urlize(domain_name)
        expected = '<a href="http://home.corp.redhat.com" ' \
                   'rel="nofollow">http://home.corp.redhat.com</a>'
        self.assertEqual(result, expected)

    def test_redhat_url_with_querystring(self):
        url = 'https://bugzilla.redhat.com/show_bug.cgi?id=519029'
        result = redhat_urlize(url)
        expected = '<a href="https://bugzilla.redhat.com/' \
                   'show_bug.cgi?id=519029" rel="nofollow">' \
                   'https://bugzilla.redhat.com/show_bug.cgi?id=519029</a>'
        self.assertEqual(result, expected)

    def test_only_domain_not_ends_with_redhat_com(self):
        domain_name = 'www.amazon.com'
        result = redhat_urlize(domain_name)
        self.assertEqual(result, domain_name, 'This should not be urlized.')

        domain_name = 'http://weibo.com'
        result = redhat_urlize(domain_name)
        self.assertEqual(result, domain_name, 'This should not be urlized.')

    def test_domain_in_the_middle(self):
        domain_name = ' http://www.redhat.com '
        result = redhat_urlize(domain_name)
        expected = ' <a href="http://www.redhat.com" ' \
                   'rel="nofollow">http://www.redhat.com</a> '
        self.assertEqual(result, expected)

        domain_name = ' http://www.redhat.com'
        result = redhat_urlize(domain_name)
        expected = ' <a href="http://www.redhat.com" ' \
                   'rel="nofollow">http://www.redhat.com</a>'
        self.assertEqual(result, expected)

        domain_name = 'http://www.redhat.com '
        result = redhat_urlize(domain_name)
        expected = '<a href="http://www.redhat.com" ' \
                   'rel="nofollow">http://www.redhat.com</a> '
        self.assertEqual(result, expected)

        domain_name = '<p>www.redhat.com</p>'
        result = redhat_urlize(domain_name)
        expected = '<p><a href="http://www.redhat.com" ' \
                   'rel="nofollow">www.redhat.com</a></p>'
        self.assertEqual(result, expected,
                         '\"%s\" should be urlized. This is the bug of '
                         'django\'s urlize. Here just IGNORE it.'
                         % domain_name)

        domain_name = '<p> www.redhat.com </p>'
        result = redhat_urlize(domain_name)
        expected = '<p> <a href="http://www.redhat.com">' \
                   'www.redhat.com</a> </p>'
        self.assertEqual(result, expected)

        domain_name = 'xxx www.redhat.com <'
        result = redhat_urlize(domain_name)
        expected = 'xxx <a href="http://www.redhat.com" ' \
                   'rel="nofollow">www.redhat.com</a> <'
        self.assertEqual(result, expected)

    def test_domain_not_ends_with_redhat_com_in_the_middle(self):
        domain_name = ' http://www.google.com '
        result = redhat_urlize(domain_name)
        expected = domain_name
        self.assertEqual(result, expected)

        domain_name = '<p>www.google.com</p>'
        result = redhat_urlize(domain_name)
        expected = domain_name
        self.assertEqual(result, expected)

        domain_name = '<p> www.google.com </p>'
        result = redhat_urlize(domain_name)
        expected = domain_name
        self.assertEqual(result, expected)

        domain_name = 'xxx www.google.com <'
        result = redhat_urlize(domain_name)
        expected = domain_name
        self.assertEqual(result, expected)

    def test_only_email_link_redhat(self):
        addr = 'cqi@redhat.com'
        result = redhat_urlize(addr)
        expected = '<a href="mailto:cqi@redhat.com">cqi@redhat.com</a>'
        self.assertEqual(result, expected)

    def test_only_email_link_not_redhat(self):
        addr = 'qcxhome@gmail.com'
        result = redhat_urlize(addr)
        expected = '<a href="mailto:qcxhome@gmail.com">qcxhome@gmail.com</a>'
        self.assertEqual(result, expected)

    def test_email_link_redhat_in_the_middle(self):
        addr = ' cqi@redhat.com '
        result = redhat_urlize(addr)
        expected = ' <a href="mailto:cqi@redhat.com">cqi@redhat.com</a> '
        self.assertEqual(result, expected)

        addr = ' cqi@redhat.com'
        result = redhat_urlize(addr)
        expected = ' <a href="mailto:cqi@redhat.com">cqi@redhat.com</a>'
        self.assertEqual(result, expected)

        addr = 'cqi@redhat.com '
        result = redhat_urlize(addr)
        expected = '<a href="mailto:cqi@redhat.com">cqi@redhat.com</a> '
        self.assertEqual(result, expected)

        addr = '<p> cqi@redhat.com</p>'
        result = redhat_urlize(addr)
        expected = '<p> <a href="mailto:cqi@redhat.com">cqi@redhat.com</a></p>'
        self.assertEqual(result, expected,
                         'urlized result: %s. This is the urlize\'s bug of '
                         'djanog urlize. Just IGNORE this.' % result)


if __name__ == '__main__':
    unittest.main()
