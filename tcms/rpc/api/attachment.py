# -*- coding: utf-8 -*-

from attachments.views import delete_attachment
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.rpc.decorators import permissions_required

__all__ = ("remove_attachment",)


@permissions_required("attachments.delete_attachment")
@rpc_method(name="Attachment.remove_attachment")
def remove_attachment(attachment_id, **kwargs):
    """
    .. function:: RPC Attachment.remove_attachment(attachment_id)

        Remove the given attachment file.

        :param attachment_id: PK of attachment to remove
        :type attachment_id: int
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :raises Exception: if attachment doesn't exist,
                 InternalError or removal fails
    """
    request = kwargs.get(REQUEST_KEY)
    response = delete_attachment(request, attachment_id)
    if response.status_code == 404:
        raise Exception("Removing attachment %d failed" % attachment_id)
