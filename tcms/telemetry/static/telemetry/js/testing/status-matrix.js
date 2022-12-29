import { jsonRPC } from '../../../../../static/js/jsonrpc'

let table
const initialColumn = {
    data: null,
    className: 'table-view-pf-actions',
    render: function (data, type, full, meta) {
        const caseId = data.case_id

        return '<span style="padding: 5px;">' +
            `<a href="/case/${caseId}/">TC-${caseId}: ${data.case__summary}</a>` +
            '</span>'
    }
}

export function initializePage () {
    document.getElementById('id_order').onchange = drawTable
    document.getElementById('id_include_child_tps').onchange = drawTable

    $('#table').on('draw.dt', function () {
        setMaxHeight($(this))
    })

    $(window).on('resize', function () {
        setMaxHeight($('#table'))
    })
}

function setMaxHeight (t) {
    const maxH = 0.99 * (window.innerHeight - t.position().top)
    t.css('max-height', maxH)
}

export function drawTable () {
    $('.js-spinner').show()
    if (table) {
        table.destroy()

        $('table > thead > tr > th:not(.header)').remove()
        $('table > tbody > tr').remove()
    }

    const query = {}

    const productIds = $('#id_product').val()
    if (productIds.length) {
        query.run__plan__product__in = productIds
    }

    const versionIds = $('#id_version').val()
    if (versionIds.length) {
        query.run__plan__product_version__in = versionIds
    }

    const buildIds = $('#id_build').val()
    if (buildIds.length) {
        query.build_id__in = buildIds
    }

    const testPlanIds = $('#id_test_plan').val()
    const includeChildTPs = $('#id_include_child_tps').is(':checked')
    if (testPlanIds.length) {
        query.run__plan__in = testPlanIds

        // note: executed synchronously to avoid race condition between
        // collecting the list of child TPs and drawing the table below
        if (includeChildTPs) {
            jsonRPC('TestPlan.filter', { parent__in: testPlanIds }, function (result) {
                result.forEach(function (element) {
                    query.run__plan__in.push(element.id)
                })
            }, true)
        }
    }

    const dateBefore = $('#id_before')
    if (dateBefore.val()) {
        query.stop_date__lte = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
    }

    const dateAfter = $('#id_after')
    if (dateAfter.val()) {
        query.stop_date__gte = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
    }

    jsonRPC('Testing.status_matrix', query, data => {
        const tableColumns = [initialColumn]
        const testRunIds = Object.keys(data.runs)

        // reverse the TR-xy order to show newest ones first
        if (!$('#id_order').is(':checked')) {
            testRunIds.reverse()
        }

        testRunIds.forEach(testRunId => {
            const testRunSummary = data.runs[testRunId]
            $('.table > thead > tr').append(`
            <th class="header-test-run">
                <a href="/runs/${testRunId}/">TR-${testRunId}</a>
                <span class="fa pficon-help" data-toggle="tooltip" data-placement="bottom" title="${testRunSummary}"></span>
            </th>`)

            tableColumns.push({
                data: null,
                sortable: false,
                render: renderData(testRunId, testPlanIds, includeChildTPs, data)
            })
        })

        table = $('#table').DataTable({
            columns: tableColumns,
            data: data.cases,
            paging: false,
            ordering: false,
            dom: 't',
            language: {
                loadingRecords: '<div class="spinner spinner-lg"></div>',
                processing: '<div class="spinner spinner-lg"></div>',
                zeroRecords: 'No records found'
            }
        })

        const cells = $('.table > tbody > tr > td:has(.execution-status)')
        Object.entries(cells).forEach(applyStyleToCell)

        // initialize the tooltips by hand, because they are dinamically inserted
        // and not handled by Bootstrap itself
        $('span[data-toggle=tooltip]').tooltip()

        $('.js-spinner').hide()
    })
}

function applyStyleToCell (cell) {
    const cellElement = cell[1]
    if (cellElement) {
        const cellChildren = cellElement.children
        if (cellChildren) {
            const el = cellChildren[0]
            if (el && el.attributes.color) {
                const color = el.attributes.color.nodeValue
                $(cell[1]).attr('style', `border-left: 5px solid ${color}`)
                if (el.attributes['from-parent'].nodeValue === 'true') {
                    $(cell[1]).addClass('danger')
                }
            }
        }
    }
}

function renderData (testRunId, testPlanIds, includeChildTPs, apiData) {
    return (data, type, row, meta) => {
        const execution = apiData.executions[`${data.case_id}-${testRunId}`]

        if (execution) {
            const statusColor = apiData.statusColors[execution.status_id]
            const planId = apiData.plans[testRunId]
            const fromParentTP = includeChildTPs && testPlanIds.includes(planId)
            let iconClass = ''

            if (fromParentTP) {
                iconClass = 'fa fa-arrow-circle-o-up'
            }

            return `<span class="execution-status ${iconClass}" color="${statusColor}" from-parent="${fromParentTP}"> ` +
                `<a href="/runs/${execution.run_id}/#test-execution-${execution.pk}">TE-${execution.pk}</a>` +
                '</span>'
        }
        return ''
    }
}
