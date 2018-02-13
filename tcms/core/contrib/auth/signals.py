"""
Defines signals which are sent when authentication actions occur.

.. data:: user_registered

    Sent when a new user is registered into Kiwi TCMS through any of the
    backends which support user registration. The signal receives three parameters:
    ``request``, ``user`` and ``backend`` respectively!
"""

from django.dispatch import Signal

user_registered = Signal(providing_args=['user', 'backend'])
