# -*- coding: utf-8 -*-
from tcms.integration.djqpid.settings import ENABLE_MESSAGING

'''
Message Bus is controlled by ENABLE_MESSAGING variable defined in settings.
If the messaging is not enabled, no signal will be registered here.
'''

if ENABLE_MESSAGING:
    '''
    Register signals here. These signal handler will
    handle the message sending and the related data
    '''

    # TODO: add signal handler here
