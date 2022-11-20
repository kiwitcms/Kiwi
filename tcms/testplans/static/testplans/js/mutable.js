import { populateVersion } from '../../../../static/js/utils'

/*
    Used in mutable.html and clone.html
*/
export function pageTestplansMutableReadyHandler () {
    if ($('#page-testplans-mutable').length === 0) {
        return
    }

    if ($('#id_version').find('option').length === 0) {
        populateVersion()
    }

    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_version').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('.selectpicker').selectpicker()

    $('.bootstrap-switch').bootstrapSwitch()

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh')
        populateVersion()
    }

    document.getElementById('id_version').onchange = function () {
        $('#id_version').selectpicker('refresh')
    }
}
