import { initializeDateTimePicker } from '../../../../static/js/datetime_picker'
import { dataTableJsonRPC, jsonRPC } from '../../../../static/js/jsonrpc'
import { exportButtons } from '../../../../static/js/datatables_common'
import {
    escapeHTML, updateComponentSelectFromProduct, updateCategorySelectFromProduct,
    updateParamsToSearchTags, updateTestPlanSelectFromProduct
} from '../../../../static/js/utils'

function preProcessData (data, callbackF) {
    const caseIds = []
    data.forEach(function (element) {
        caseIds.push(element.id)
    })

    // get tags for all objects
    const tagsPerCase = {}
    jsonRPC('Tag.filter', { case__in: caseIds }, function (tags) {
        tags.forEach(function (element) {
            if (tagsPerCase[element.case] === undefined) {
                tagsPerCase[element.case] = []
            }

            // push only if unique
            if (tagsPerCase[element.case].indexOf(element.name) === -1) {
                tagsPerCase[element.case].push(element.name)
            }
        })

        // get components for all objects
        const componentsPerCase = {}
        jsonRPC('Component.filter', { cases__in: caseIds }, function (components) {
            components.forEach(function (element) {
                if (componentsPerCase[element.cases] === undefined) {
                    componentsPerCase[element.cases] = []
                }

                // push only if unique
                if (componentsPerCase[element.cases].indexOf(element.name) === -1) {
                    componentsPerCase[element.cases].push(element.name)
                }
            })

            // augment data set with additional info
            data.forEach(function (element) {
                if (element.id in tagsPerCase) {
                    element.tag_names = tagsPerCase[element.id]
                } else {
                    element.tag_names = []
                }

                if (element.id in componentsPerCase) {
                    element.component_names = componentsPerCase[element.id]
                } else {
                    element.component_names = []
                }
            })

            callbackF({ data }) // renders everything
        })
    })
}

export function pageTestcasesSearchReadyHandler () {
    initializeDateTimePicker('#id_before')
    initializeDateTimePicker('#id_after')

    const table = $('#resultsTable').DataTable({
        pageLength: $('#navbar').data('defaultpagesize'),
        ajax: function (data, callbackF, settings) {
            const params = {}

            if ($('#id_summary').val()) {
                params.summary__icontains = $('#id_summary').val()
            }

            if ($('#id_before').val()) {
                params.create_date__lte = $('#id_before').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
            }

            if ($('#id_after').val()) {
                params.create_date__gte = $('#id_after').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
            }

            if ($('#id_product').val()) {
                params.category__product = $('#id_product').val()
            };

            if ($('#id_category').val()) {
                params.category = $('#id_category').val()
            };

            if ($('#id_component').val()) {
                params.component = $('#id_component').val()
            };

            if ($('#id_priority').val().length > 0) {
                params.priority__in = $('#id_priority').val()
            };

            if ($('#id_status').val().length > 0) {
                params.case_status__in = $('#id_status').val()
            };

            if ($('#id_author').val()) {
                params.author__username__startswith = $('#id_author').val()
            };

            if ($('#id_run').val()) {
                params.executions__run__in = [$('#id_run').val()]
            };

            const testPlanIds = selectedPlanIds()
            if (testPlanIds.length) {
                params.plan__in = testPlanIds
            }

            if ($('input[name=is_automated]:checked').val() === 'true') {
                params.is_automated = true
            };

            if ($('input[name=is_automated]:checked').val() === 'false') {
                params.is_automated = false
            };

            const text = $('#id_text').val()
            if (text) {
                params.text__icontains = text
            };

            updateParamsToSearchTags('#id_tag', params)

            dataTableJsonRPC('TestCase.filter', params, callbackF, preProcessData)
        },
        select: {
            className: 'success',
            style: 'multi',
            selector: 'td > input'
        },
        columns: [
            {
                data: null,
                sortable: false,
                orderable: false,
                target: 1,
                className: 'js-select-checkbox noVis',
                render: function (data, type, full, meta) {
                    return `<input type="checkbox" value="${data.id}" name="row-check">`
                }
            },
            { data: 'id' },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/case/' + data.id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>'
                }
            },
            { data: 'create_date' },
            { data: 'category__name' },
            { data: 'component_names' },
            { data: 'priority__value' },
            { data: 'case_status__name' },
            { data: 'is_automated' },
            { data: 'author__username' },
            { data: 'tag_names' }
        ],
        dom: 'Bptp',
        buttons: exportButtons,
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: 'No records found'
        },
        order: [[1, 'asc']]
    })

    // hide the select checkboxes if not in use
    if (window.location.href.indexOf('allow_select') === -1) {
        table.on('draw.dt', function () {
            $('.js-select-checkbox').hide()
        })
    }

    const selectAllButton = $('#check-all')

    selectAllButton.click(function () {
        const rowCheckboxInputButton = $("input:checkbox[name='row-check']")
        const isChecked = selectAllButton.prop('checked')
        rowCheckboxInputButton.prop('checked', isChecked)
        isChecked ? table.rows().select() : table.rows().deselect()
    })

    table.on('select', function (e, dt, type, indexes) {
        if (type === 'row') {
            const totalRows = $("input:checkbox[name='row-check']").length
            const selectedRows = $("input:checkbox[name='row-check']:checked").length
            selectAllButton.prop('checked', totalRows === selectedRows)
        }
    })

    table.on('deselect', function (e, dt, type, indexes) {
        if (type === 'row') {
            selectAllButton.prop('checked', false)
        }
    })

    $('#select-btn').click(function (event) {
        event.preventDefault()
        const testCaseIDs = []

        table.rows({ selected: true }).data().each(function (selected) {
            testCaseIDs.push(selected.id)
        })

        if (testCaseIDs && window.opener) {
            window.opener.addTestCases(testCaseIDs, window)
        }

        return false
    })

    $('#btn_search').click(function () {
        table.ajax.reload()
        return false // so we don't actually send the form
    })

    $('#id_product').change(function () {
        updateComponentSelectFromProduct()
        updateCategorySelectFromProduct()
        updateTestPlanSelectFromProduct({ parent: null }, discoverNestedTestPlans)
    })

    $('#id_test_plan').change(function () {
        $(this).parents('.bootstrap-select').toggleClass('open')
    })

    if (window.location.href.indexOf('product') > -1) {
        $('#id_product').change()
    }
}

export function discoverNestedTestPlans (inputData, callbackF) {
    const prefix = '&nbsp;&nbsp;&nbsp;&nbsp;'
    const result = []

    inputData.forEach((parent) => {
        result.push(parent)

        if (parent.children__count > 0) {
            jsonRPC('TestPlan.tree', parent.id, (children) => {
                children.forEach((child) => {
                    if (child.tree_depth > 0) {
                        child.name = prefix.repeat(child.tree_depth) + child.name
                        // TestPlan.tree() method doesn't return product name!
                        // Also note that entries in the Select are ordered by Product
                        // and if the child has a different product than the parent
                        // that would break the ordering scheme! That's why explicitly
                        // set the value even if it can be a bit inaccurate sometimes.
                        child.product__name = parent.product__name
                        result.push(child)
                    }
                })
            }, true)
        }
    })

    callbackF(result)
}

function selectedPlanIds () {
    const selectedIds = $('#id_test_plan').val()
    const childIds = []

    // search for children of each selected TP
    if ($('#id_include_child_tps').is(':checked')) {
        for (const id of selectedIds) {
            const option = $(`#id_test_plan option[value="${id}"]`)[0]

            // scan all DOM elements after the selected one for child test plans
            // b/c they are rendered as subsequent <options> with different
            // leading space indentation
            let sibling = option.nextElementSibling
            const indentation = option.text.search(/\S|$/)

            while (sibling !== null && sibling.text.search(/\S|$/) > indentation) {
                // everything that starts with a space is considered a child TP
                childIds.push(sibling.value)
                sibling = sibling.nextElementSibling
            }
        }
    }

    return selectedIds.concat(childIds)
}
