import { dataTableJsonRPC, jsonRPC } from '../../../../../static/js/jsonrpc'
import { exportButtons } from '../../../../../static/js/datatables_common'
import { escapeHTML } from '../../../../../static/js/utils'

export function initializePage () {
    document.getElementById('id_include_child_tps').onchange = drawTable
}

function preProcessData (data, callbackF) {
    const caseIds = []
    const runIds = []
    data.forEach(function (element) {
        caseIds.push(element.case)
        runIds.push(element.run)
    })

    jsonRPC('TestCase.filter', { pk__in: caseIds }, function (cases) {
        const testerPerCase = {}
        cases.forEach(function (element) {
            testerPerCase[element.id] = element.default_tester__username
        })

        jsonRPC('TestRun.filter', { pk__in: runIds }, function (runs) {
            const testerPerRun = {}
            runs.forEach(function (element) {
                testerPerRun[element.id] = element.default_tester__username
            })

            // augment data set with additional info
            data.forEach(function (element) {
                element.default_tester__from_case = testerPerCase[element.case]
                element.default_tester__from_run = testerPerRun[element.run]
            })

            callbackF({ data }) // renders everything
        })
    })
}

export function drawTable () {
    $('#resultsTable').DataTable({
        pageLength: $('#navbar').data('defaultpagesize'),
        ajax: function (data, callbackF, settings) {
            const query = {}

            const productIds = $('#id_product').val()
            if (productIds.length) {
                query.build__version__product__in = productIds
            }

            const versionIds = $('#id_version').val()
            if (versionIds.length) {
                query.build__version__in = versionIds
            }

            const buildIds = $('#id_build').val()
            if (buildIds.length) {
                query.build__in = buildIds
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

            const testRunSummary = $('#id_test_run_summary').val()
            if (testRunSummary) {
                query.run__summary__icontains = testRunSummary
            }

            dataTableJsonRPC('TestExecution.filter', query, callbackF, preProcessData)
        },
        select: {
            className: 'success',
            style: 'multi',
            selector: 'td > input'
        },
        columns: [
            {
                data: null,
                render: function (data, type, full, meta) {
                    return `<a href="/runs/${data.run}/#test-execution-${data.id}">TE-${data.id}</a>`
                }
            },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/case/' + data.case + '/" >' + escapeHTML(data.case__summary) + '</a>'
                }
            },
            {
                data: null,
                render: function (data, type, full, meta) {
                    const statusName = escapeHTML(data.status__name)
                    const statusColor = escapeHTML(data.status__color)
                    const statusIcon = escapeHTML(data.status__icon)

                    return `<span style="color: ${statusColor}; white-space: nowrap"><span class="${statusIcon}"></span> ${statusName}</span>`
                }
            },
            {
                data: 'build__name'
            },
            {
                data: 'default_tester__from_case'
            },
            {
                data: 'default_tester__from_run'
            },
            {
                data: 'assignee__username'
            },
            {
                data: 'tested_by__username'
            },
            {
                data: 'start_date'
            },
            {
                data: 'stop_date'
            }
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
}
