import { testPlanAutoComplete } from '../../../../static/js/jsonrpc'
import { populateVersion } from '../../../../static/js/utils'

const planCache = {}

/*
    Used in mutable.html and clone.html
*/
export function pageTestplansMutableReadyHandler () {
    if ($('#id_version').find('option').length === 0) {
        populateVersion()
    }

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

    // autocomplete for Parent ID
    testPlanAutoComplete('#input-select-parent', planCache)

    // NOTE: keydown() instead of keyup() to prevent submitting the form
    $('#input-select-parent').keydown(function (event) {
        if (event.keyCode === 13) {
            const planName = this.value
            const plan = planCache[planName]

            // empty value + Enter clears the existing selection
            const planId = plan !== undefined ? plan.id : null

            $('#id_parent').val(planId)
            $('.js-parent-id-value').text(planId)

            event.preventDefault()
            return false
        };
    })

    // override the default inline-block style
    $('span.twitter-typeahead').css('display', 'block')
}
