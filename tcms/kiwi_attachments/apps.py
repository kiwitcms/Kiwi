from attachments.apps import AttachmentsConfig

from . import validators


class AppConfig(AttachmentsConfig):
    """
    Defines custom form validators!
    """

    attachment_validators = (
        validators.deny_uploads_ending_in_dot_exe,
        validators.deny_uploads_containing_script_tag,
    )
