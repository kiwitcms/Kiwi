import { initDuplicateCheck, updateCategorySelectFromProduct } from '../../../../static/js/utils'

export function pageTestcasesMutableReadyHandler () {
    $('#id_template').change(function () {
        window.markdownEditor.codemirror.setValue($(this).val())
    })

    $('#add_id_template').click(function () {
        // note: will not refresh the selected value
        return showRelatedObjectPopup(this)
    })

    if ($('#id_category').find('option').length === 0) {
        populateProductCategory()
    }

    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_category').click(function () {
        return showRelatedObjectPopup(this)
    })

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh')
        populateProductCategory()
    }

    document.getElementById('id_category').onchange = function () {
        $('#id_category').selectpicker('refresh')
    }

    $('.duration-picker').durationPicker({
        translations: {
            day: $('html').data('trans-day'),
            days: $('html').data('trans-days'),

            hour: $('html').data('trans-hour'),
            hours: $('html').data('trans-hours'),

            minute: $('html').data('trans-minute'),
            minutes: $('html').data('trans-minutes'),

            second: $('html').data('trans-second'),
            seconds: $('html').data('trans-seconds')
        },

        showDays: true,
        showHours: true,
        showMinutes: true,
        showSeconds: true
    })

    initDuplicateCheck({
        rpcMethod: 'TestCase.filter',
        fieldName: 'summary',
        inputSelector: '#id_summary',
        groupSelector: '#summary-group',
        warningSelector: '#duplicate-summary-warning',
        autocompleteSelector: '#summary-autocomplete',
        modalSelector: '#duplicate-modal',
        prefix: 'TC',
        detailUrlBase: '/case/',
        descriptionField: 'text',
        modalRows: function (g, tc) {
            return [
                [g('trans-duplicate-modal-summary'), tc.summary],
                [g('trans-duplicate-modal-status'), tc.case_status__name],
                [g('trans-duplicate-modal-category'), tc.category__name],
                [g('trans-duplicate-modal-priority'), tc.priority__value],
                [g('trans-duplicate-modal-author'), tc.author__username]
            ]
        }
    })
}

function populateProductCategory () {
    const productId = $('#id_product').val()

    if (productId === null) {
        $('#add_id_category').addClass('disabled')
    } else {
        $('#add_id_category').removeClass('disabled')
    }

    const href = $('#add_id_category')[0].href
    $('#add_id_category')[0].href = href.slice(0, href.indexOf('&product'))
    $('#add_id_category')[0].href += `&product=${productId}`
    $('#id_category').find('option').remove()
    updateCategorySelectFromProduct()
}
