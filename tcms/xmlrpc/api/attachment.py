# -*- coding: utf-8 -*-

from attachments.views import delete_attachment
from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'remove_attachment',
)


@permissions_required('attachments.delete_attachment')
@rpc_method(name='Attachment.remove_attachment')
def remove_attachment(attachment_id, **kwargs):
    """
    .. function:: XML-RPC Attachment.remove_attachment(attachment_id)

        Remove the given attachment file.

        :param attachment_id: PK of attachment to remove
        :type attachment_id: int
        :return: None
        :raises: Exception if attachment doesn't exist,
                 InternalError or removal fails
    """
    request = kwargs.get(REQUEST_KEY)
    response = delete_attachment(request, attachment_id)
    if response.status_code == 404:
        raise Exception("Removing attachment %d failed" % attachment_id)
