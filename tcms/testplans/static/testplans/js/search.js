import { initializeDateTimePicker } from '../../../../static/js/datetime_picker'
import { dataTableJsonRPC, jsonRPC } from '../../../../static/js/jsonrpc'
import {
    escapeHTML,
    updateParamsToSearchTags, updateVersionSelectFromProduct
} from '../../../../static/js/utils'
import { hookIntoPagination } from '../../../../static/js/pagination'

function preProcessData (data, callbackF) {
    const planIds = []
    data.forEach(function (element) {
        planIds.push(element.id)
    })

    // get tags for all objects
    const tagsPerPlan = {}
    jsonRPC('Tag.filter', { plan__in: planIds }, function (tags) {
        tags.forEach(function (element) {
            if (tagsPerPlan[element.plan] === undefined) {
                tagsPerPlan[element.plan] = []
            }

            // push only if unique
            if (tagsPerPlan[element.plan].indexOf(element.name) === -1) {
                tagsPerPlan[element.plan].push(element.name)
            }
        })

        // augment data set with additional info
        data.forEach(function (element) {
            if (element.id in tagsPerPlan) {
                element.tag = tagsPerPlan[element.id]
            } else {
                element.tag = []
            }
        })

        callbackF({ data }) // renders everything
    })
}

export function pageTestplansSearchReadyHandler () {
    initializeDateTimePicker('#id_before')
    initializeDateTimePicker('#id_after')

    const table = $('#resultsTable').DataTable({
        pageLength: $('#navbar').data('defaultpagesize'),
        ajax: function (data, callbackF, settings) {
            const params = {}

            if ($('#id_name').val()) {
                params.name__icontains = $('#id_name').val()
            }

            if ($('#id_before').val()) {
                params.create_date__lte = $('#id_before').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
            }

            if ($('#id_after').val()) {
                params.create_date__gte = $('#id_after').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
            }

            if ($('#id_product').val()) {
                params.product = $('#id_product').val()
            };

            if ($('#id_version').val()) {
                params.product_version = $('#id_version').val()
            };

            if ($('#id_type').val()) {
                params.type = $('#id_type').val()
            };

            if ($('#id_author').val()) {
                params.author__username__startswith = $('#id_author').val()
            };

            if ($('#id_default_tester').val()) {
                params.cases__default_tester__username__startswith = $('#id_default_tester').val()
            };

            updateParamsToSearchTags('#id_tag', params)

            params.is_active = $('#id_active').is(':checked')

            dataTableJsonRPC('TestPlan.filter', params, callbackF, preProcessData)
        },
        columns: [
            { data: 'id' },
            {
                data: null,
                render: function (data, type, full, meta) {
                    let result = '<a href="/plan/' + data.id + '/">' + escapeHTML(data.name) + '</a>'
                    if (!data.is_active) {
                        result = '<strike>' + result + '</strike>'
                    }
                    return result
                }
            },
            { data: 'create_date' },
            { data: 'product__name' },
            { data: 'product_version__value' },
            { data: 'type__name' },
            { data: 'author__username' },
            { data: 'tag' }
        ],
        dom: 't',
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: 'No records found'
        },
        order: [[0, 'asc']]
    })

    hookIntoPagination('#resultsTable', table)

    $('#btn_search').click(function () {
        table.ajax.reload()
        return false // so we don't actually send the form
    })

    $('#id_product').change(updateVersionSelectFromProduct)
}
