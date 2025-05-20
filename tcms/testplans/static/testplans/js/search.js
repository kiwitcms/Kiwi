import { initializeDateTimePicker } from '../../../../static/js/datetime_picker'
import { dataTableJsonRPC, jsonRPC } from '../../../../static/js/jsonrpc'
import { exportButtons } from '../../../../static/js/datatables_common'
import {
    escapeHTML,
    updateParamsToSearchTags, updateVersionSelectFromProduct
} from '../../../../static/js/utils'

let testPlanIdsFromBackend = []
let hiddenChildRows = {}

function preProcessData (data, callbackF) {
    testPlanIdsFromBackend = []
    hiddenChildRows = {}

    data.forEach(function (element) {
        testPlanIdsFromBackend.push(element.id)
    })

    // get tags for all objects
    const tagsPerPlan = {}
    jsonRPC('Tag.filter', { plan__in: testPlanIdsFromBackend }, function (tags) {
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

    const multiCloneButton = {
        text: '<i class="fa fa-code-fork"></i>',
        titleAttr: 'Clone Selected',
        action: function (e, dt, node, config) {
            const selectedTestPlans = getSelectedTestPlans()
            if (selectedTestPlans.length === 0) {
                alert($('#main-element').data('trans-no-testplans-selected'))
                return false
            }

            window.location.assign(`/plan/clone/?p=${selectedTestPlans.join('&p=')}`)
        }
    }

    const rowsNotShownMessage = $('#main-element').data('trans-some-rows-not-shown')
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
            {
                data: null,
                orderable: false,
                render: function () { return '<input type="checkbox" class="row-select">' }
            },
            {
                data: null,
                defaultContent: '',
                orderable: false,
                className: 'noVis',
                createdCell: function (td, cellData, rowData, rowIndex, colIndex) {
                    if (rowData.children__count > 0) {
                        $(td).addClass('dt-control')
                    }
                }
            },
            { data: 'id' },
            {
                data: null,
                render: function (data, type, full, meta) {
                    let result = '<a href="/plan/' + data.id + '/">' + escapeHTML(data.name) + '</a>'
                    result = result + ` <span class="pficon pficon-rebalance children-not-shown-message" title="${rowsNotShownMessage}"></span>`
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
        rowCallback: function (row, data, index) {
            $(row).addClass(`test-plan-row-${data.id}`)

            // is this is a child row and it's parent is also in the result set
            // then hide it b/c it will be shown via expansion of the parent row
            if (testPlanIdsFromBackend.indexOf(data.parent) > -1) {
                if (!hiddenChildRows[data.parent]) {
                    hiddenChildRows[data.parent] = []
                }
                hiddenChildRows[data.parent].push(row)
                $(row).hide()
                // WARNING: using .hide() may mess up pagination but makes it
                // very easy to display child rows afterwards! Not a big issue for now.
            }
        },
        drawCallback: function (settings) {
            const data = this.api().data()
            $('.children-not-shown-message').hide()

            data.each(function (row) {
                if (row.children__count) {
                    const selectedChildren = hiddenChildRows[row.id] ? hiddenChildRows[row.id] : []

                    // some children are filtered out, display imbalance icon
                    if (row.children__count > selectedChildren.length) {
                        $(`.test-plan-row-${row.id} .children-not-shown-message`).show()
                    }

                    // all children filtered out, hide +/- button
                    if (selectedChildren.length === 0) {
                        $(`.test-plan-row-${row.id} .dt-control`).toggleClass('dt-control')
                    }
                }
            })
        },
        dom: 'Bptp',
        buttons: [
            multiCloneButton,
            ...exportButtons
        ],
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: 'No records found'
        },
        order: [[2, 'asc']],
        initComplete: function () {
            const btnContainer = table.buttons().container()
            $(btnContainer).prepend(
                '<input type="checkbox" id="onlyActive" style=" margin: 0 10px;">'
            )

            // Hook the checkbox change event to “select all”
            $('#onlyActive').on('change', function () {
                const checked = this.checked
                $('#resultsTable tbody input.row-select')
                    .prop('checked', checked)
                    .trigger('change')
            })
        }
    })

    // row checkbox handler
    $('#resultsTable tbody').on('change', 'input.row-select', function () {
        const $tr = $(this).closest('tr')
        if (this.checked) table.row($tr).select()
        else table.row($tr).deselect()
    })

    // Add event listener for opening and closing nested test plans
    $('#resultsTable').on('click', 'td.dt-control', function () {
        const bracket = $(this).find('span')
        const tr = $(this).closest('tr')
        const row = table.row(tr)

        if (row.child.isShown()) {
            hideExpandedChildren(table, row)
            row.child.hide()
            bracket.removeClass('fa-angle-down')
        } else {
            row.child(renderChildrenOf(tr, row.data())).show()
            bracket.addClass('fa-angle-down')
        }
    })

    $('#btn_search').click(function () {
        table.ajax.reload()
        return false // so we don't actually send the form
    })

    $('#id_product').change(updateVersionSelectFromProduct)
}

function getSelectedTestPlans () {
    const inputs = $('#resultsTable tbody input.row-select:checked').closest('tr:visible')
    const tpIds = []

    inputs.each(function (_, el) {
        // Check if the row has collapsed children and add their IDs
        tpIds.push(...getChildRows(el))
    })
    return tpIds
}

function getChildRows (parentRowId) {
    const tpIds = []
    const parentRow = $('#resultsTable').DataTable().row($(parentRowId).closest('tr'))
    const id = $(parentRowId).closest('tr').find('td:nth-child(3)').text().trim()
    const children = hiddenChildRows[id]

    if (id) {
        tpIds.push(id)
    }

    if (children && !parentRow.child.isShown()) {
        children.forEach(function (childRow) {
            tpIds.push(...getChildRows(childRow))
        })
        return tpIds
    }
    return tpIds
}

function hideExpandedChildren (table, parentRow) {
    const children = hiddenChildRows[parentRow.data().id]
    children.forEach(
        function (element) {
            const row = table.row($(element))
            if (row.child.isShown()) {
                row.child.hide()
            }
            if (hiddenChildRows[row.data().id]) {
                hideExpandedChildren(table, row)
            }
        }
    )
}

function renderChildrenOf (parentRow, data) {
    const parentPadding = $(parentRow).find('td').css('padding-left').replace('px', '')
    const childPadding = parseInt(parentPadding) + 5

    // this is an array of previously hidden rows
    const children = hiddenChildRows[data.id]
    $(children).find('td').css('border', '0').css('padding-left', `${childPadding}px`)

    if ($(parentRow).find('input.row-select').prop('checked')) {
        $(children).find('input.row-select').prop('checked', true).trigger('change')
    }

    return $(children).show()
}
