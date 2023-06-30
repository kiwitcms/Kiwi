from bleach_allowlist import generally_xss_unsafe
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _


def deny_uploads_containing_script_tag(uploaded_file):
    for chunk in uploaded_file.chunks(2048):
        for tag_name in generally_xss_unsafe:
            if chunk.lower().find(b"<" + tag_name.encode()) > -1:
                raise ValidationError(_(f"File contains forbidden tag: <{tag_name}>"))

        for attr_name in (
            # attributes
            "onabort",
            "onafterprint",
            "onbeforeprint",
            "onbeforeunload",
            "onblur",
            "oncanplay",
            "oncanplaythrough",
            "onchange",
            "onclick",
            "oncontextmenu",
            "oncopy",
            "oncuechange",
            "oncut",
            "ondblclick",
            "ondrag",
            "ondragend",
            "ondragenter",
            "ondragleave",
            "ondragover",
            "ondragstart",
            "ondrop",
            "ondurationchange",
            "onemptied",
            "onended",
            "onerror",
            "onerror",
            "onfocus",
            "onhashchange",
            "oninput",
            "oninvalid",
            "onkeydown",
            "onkeypress",
            "onkeyup",
            "onload",
            "onloadeddata",
            "onloadedmetadata",
            "onloadstart",
            "onmessage",
            "onmousedown",
            "onmousemove",
            "onmouseout",
            "onmouseover",
            "onmouseup",
            "onmousewheel",
            "onoffline",
            "ononline",
            "onpagehide",
            "onpageshow",
            "onpaste",
            "onpause",
            "onplay",
            "onplaying",
            "onpopstate",
            "onprogress",
            "onratechange",
            "onreset",
            "onresize",
            "onscroll",
            "onsearch",
            "onseeked",
            "onseeking",
            "onselect",
            "onstalled",
            "onstorage",
            "onsubmit",
            "onsuspend",
            "ontimeupdate",
            "ontoggle",
            "onunload",
            "onvolumechange",
            "onwaiting",
            "onwheel",
            # URL schemes
            "data:",
            "javascript:",
        ):
            if chunk.lower().find(attr_name.encode()) > -1:
                raise ValidationError(
                    _(f"File contains forbidden attribute: `{attr_name}`")
                )


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
