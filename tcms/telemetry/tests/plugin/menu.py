from django.urls import reverse_lazy


#: Follows the format of ``tcms.settings.common.MENU_ITEMS``
MENU_ITEMS = [
    ('Fake Plugin under TELEMETRY', reverse_lazy('a_fake_plugin-example_view')),
    ('Fake Plugin sub-menu', [
        ('Example', reverse_lazy('a_fake_plugin-example_view')),
        ('-', '-'),
        ('3rd level menu', [
            ('Go to Dashboard', '/'),
            ('Go to kiwitcms.org', 'http://kiwitcms.org'),
        ]),
    ]),
]
