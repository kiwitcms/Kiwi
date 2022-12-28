import { populateBuild, populateVersion } from '../../../../static/js/utils'

export function pageBugsMutableReadyHandler () {
    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_version').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_build').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_severity').click(function () {
        return showRelatedObjectPopup(this)
    })

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh')
        populateVersion()
    }

    document.getElementById('id_version').onchange = function () {
        $('#id_version').selectpicker('refresh')
        populateBuild()
    }

    document.getElementById('id_build').onchange = function () {
        $('#id_build').selectpicker('refresh')
    }

    document.getElementById('id_severity').onchange = function () {
        $('#id_severity').selectpicker('refresh')
    }

    // initialize at the end b/c we rely on .change() event to initialize builds
    if ($('#id_version').find('option').length === 0) {
        populateVersion()
    }
}
