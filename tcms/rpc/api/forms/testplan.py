from tcms.rpc.api.forms import UpdateModelFormMixin
from tcms.testplans.forms import NewPlanForm


class EditPlanForm(
    UpdateModelFormMixin, NewPlanForm
):  # pylint: disable=remove-empty-class
    pass
