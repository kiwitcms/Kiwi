# -*- coding: utf-8 -*-
from tcms.integration.djqpid import Producer
from tcms.integration.messaging.settings import ROUTING_KEY_PREFIX


class MessagingProducer(object):
    '''
    Base class for all integration class that will produce messages.

    All messaging awared integration app should inherit from this class.
    '''

    def __init__(self):
        self._producer = Producer()

    def send(self, msg, event_name, sync=True):
        ''' Begin to send message '''

        routing_key = '%s.%s' % (ROUTING_KEY_PREFIX, event_name)
        self._producer.send(msg, routing_key, sync)
