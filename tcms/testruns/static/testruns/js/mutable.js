import { initializeDateTimePicker } from '../../../../static/js/datetime_picker'
import { jsonRPC } from '../../../../static/js/jsonrpc'
import { updateSelect, updateTestPlanSelectFromProduct } from '../../../../static/js/utils'

export function pageTestrunsMutableReadyHandler () {
    initializeDateTimePicker('#id_planned_start')
    initializeDateTimePicker('#id_planned_stop')

    document.getElementById('id_product').onchange = () => {
        $('#id_product').selectpicker('refresh')
        updateTestPlanSelectFromProduct({ is_active: true })
    }

    document.getElementById('id_test_plan').onchange = () => {
        $('#id_test_plan').selectpicker('refresh')

        const updateCallback = function (data) {
            updateSelect(data, '#id_build', 'id', 'name')
        }

        const planId = $('#id_test_plan').val()
        if (planId) {
            jsonRPC('Build.filter', { version__plans: planId, is_active: true }, updateCallback)
        } else {
            updateCallback([])
        }
    }

    document.getElementById('id_build').onchange = function () {
        $('#id_build').selectpicker('refresh')
    }

    $('#add_id_build').click(function () {
        return showRelatedObjectPopup(this)
    })
}
