import os
import uuid


def read_installation_id(filename):
    with open(filename, encoding="utf-8") as file_handle:
        return file_handle.read().strip()


def check_installation_id(app_configs, **kwargs):  # pylint: disable=unused-argument
    filename = "/Kiwi/uploads/installation-id"

    if os.path.exists("/Kiwi/uploads"):
        if (not os.path.exists(filename)) or (not read_installation_id(filename)):
            with open(filename, "w", encoding="utf-8") as file_handle:
                file_handle.write(uuid.uuid4().hex)

    return []
