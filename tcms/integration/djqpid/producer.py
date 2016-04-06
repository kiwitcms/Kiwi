# -*- coding: utf-8 -*-
import os
import sys
from threading import Lock

from qpid.messaging import Connection, Message
from qpid.messaging.exceptions import ConnectionError
from qpid.messaging.exceptions import ConnectError
from qpid.messaging.exceptions import AuthenticationFailure

from tcms.integration.djqpid import settings as st
from tcms.integration.djqpid.utils import refresh_HTTP_credential_cache


errlog = sys.stderr


def errlog_writeline(log_content):
    errlog.write(log_content + os.linesep)


class Producer(object):
    ''' Core message bus '''

    _connection = None
    _session = None
    _sender = None

    _lock_for_open_connection = Lock()

    @property
    def connection(self):
        return Producer._connection

    @property
    def session(self):
        return Producer._session

    @property
    def sender(self):
        return Producer._sender

    def __connect_with_gssapi(self):
        ev_krb5ccname = 'KRB5CCNAME'
        old_ccache = os.getenv(ev_krb5ccname, None)
        new_ccache = refresh_HTTP_credential_cache()
        os.environ[ev_krb5ccname] = 'FILE:%s' % new_ccache

        options = {
            'host': st.QPID_BROKER_HOST,
            'port': st.QPID_BROKER_PORT,
            'sasl_mechanisms': st.QPID_BROKER_SASL_MECHANISMS,
            'transport': st.QPID_BROKER_TRANSPORT,
        }
        Producer._connection = Connection(**options)

        try:
            Producer._connection.open()
        finally:
            if old_ccache:
                os.environ[ev_krb5ccname] = old_ccache
            else:
                # OS has no KRB5CCNAME originally.
                # The current one is unncessary after establishing the
                # connection
                del os.environ[ev_krb5ccname]

    def __connect_as_regular(self):
        options = {
            'host': st.QPID_BROKER_HOST,
            'port': st.QPID_BROKER_PORT,
            'sasl_mechanisms': st.QPID_BROKER_SASL_MECHANISMS,
            'transport': st.QPID_BROKER_TRANSPORT,
            'username': st.AUTH_USERNAME,
            'password': st.AUTH_PASSWORD,
        }
        Producer._connection = Connection(**options)
        Producer._connection.open()

    if st.USING_GSSAPI:
        __connect_broker = __connect_with_gssapi
    else:
        __connect_broker = __connect_as_regular

    def __establish(self):
        '''
        Establish a connection to QPID broker actually.

        The connection to QPID broker is alive forever,
        unless the Apache is stopped, the broker is down,
        or even the network is unavialable.

        MessageBus also saves the session and sender for
        subsequent request of sending messages.
        '''

        self.__connect_broker()
        Producer._session = Producer._connection.session()
        Producer._sender = Producer._session.sender(st.SENDER_ADDRESS)

    def __connect_broker_if_necessary(self):
        '''
        Establishing connection to QPID broker.
        '''

        self._lock_for_open_connection.acquire()

        try:
            if not self.connection:
                self.__establish()
        finally:
            self._lock_for_open_connection.release()

    def stop(self):
        '''
        Stop the connection to the QPID broker.

        This can be considered to clear MessageBus' environment also.
        '''

        if self.sender is not None:
            Producer._sender.close()
            Producer._sender = None

        if self.session is not None:
            Producer._session.close()
            Producer._session = None

        if self.connection is not None:
            Producer._connection.close()
            Producer._connection = None

    def send(self, msg, routing_key, sync=True):
        ''' Send a message to QPID broker.  '''

        try:
            self.__connect_broker_if_necessary()

        except AuthenticationFailure, err:
            errlog_writeline(
                'AuthenticationError. Please check settings\'s configuration '
                'and your authentication environment. Error message: ' + str(
                    err))

        except ConnectError, err:
            errlog_writeline('ConnectError. ' + str(err))
            return

        try:
            o_msg = Message(msg, subject=routing_key)
            self.sender.send(o_msg, sync=sync)

        except ConnectionError, err:
            errlog_writeline('ConnectionError %s while sending message %s.' %
                             (str(err), str(o_msg)))

            self.stop()
