from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _


def deny_uploads_containing_script_tag(uploaded_file):
    for chunk in uploaded_file.chunks(2048):
        if chunk.lower().find(b"<script") > -1:
            raise ValidationError(_("File contains forbidden <script> tag"))


def deny_uploads_ending_in_dot_exe(uploaded_file):
    message = _("Uploading executable files is forbidden")

    if uploaded_file.name.find(".exe") > -1:
        raise ValidationError(message)

    if uploaded_file.content_type in [
        "application/vnd.microsoft.portable-executable",
        "application/x-dosexec",
        "application/x-ms-dos-executable",
        "application/x-msdownload",
    ]:
        raise ValidationError(message)
