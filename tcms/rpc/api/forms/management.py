from tcms.management.forms import BuildForm, ComponentForm
from tcms.rpc.api.forms import UpdateModelFormMixin


class BuildUpdateForm(  # pylint: disable=remove-empty-class,too-many-ancestors
    UpdateModelFormMixin, BuildForm
):
    pass


class ComponentUpdateForm(
    UpdateModelFormMixin, ComponentForm
):  # pylint: disable=remove-empty-class,too-many-ancestors
    pass
