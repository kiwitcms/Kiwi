// Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

// Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import { jsonRPC } from '../../../../static/js/jsonrpc'
import { populateVersion } from '../../../../static/js/utils'

export function pageTestplansCloneReadyHandler () {
    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_version').click(function () {
        return showRelatedObjectPopup(this)
    })

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh')
        populateVersion()
    }

    document.getElementById('id_version').onchange = function () {
        $('#id_version').selectpicker('refresh')
    }

    const cloneButton = $('#js-clone-button')
    cloneButton.click(function () {
        const sourcePlanId = $('#main-element').data('plan-id')
        const errorElement = $('#js-clone-error')

        const values = {
            name: $('#id_name').val(),
            product: Number($('#id_product').val()),
            version: Number($('#id_version').val()),
            copy_testcases: $('#id_copy_testcases').is(':checked')
        }

        if ($('#id_parent').is(':checked')) {
            values.parent = Number($('#id_parent').val())
        }

        cloneButton.button('loading')
        errorElement.addClass('hidden')

        jsonRPC('TestPlan.clone', [sourcePlanId, values], function (result) {
            window.location.assign(`/plan/${result.id}/`)
        }, false, function (message) {
            errorElement.text(message).removeClass('hidden')
            cloneButton.button('reset')
        })
    })
}
