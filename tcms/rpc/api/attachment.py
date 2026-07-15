from attachments.views import delete_attachment

from tcms.rpc.decorators import permissions_required
from tcms.rpc.views import rpc_method


@rpc_method(
    name="Attachment.remove_attachment",
    auth=permissions_required("attachments.delete_attachment"),
    context_target="rpc_context",
)
def remove_attachment(attachment_id, rpc_context=None):
    """
    .. function:: RPC Attachment.remove_attachment(attachment_id)

        Remove the given attachment file.

        :param attachment_id: PK of attachment to remove
        :type attachment_id: int
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :raises Exception: if attachment doesn't exist,
                 InternalError or removal fails
    """
    request = rpc_context.request
    response = delete_attachment(request, attachment_id)
    if response.status_code == 404:
        raise RuntimeError(f"Removing attachment {attachment_id} failed")
