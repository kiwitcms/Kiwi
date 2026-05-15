import { jsonRPC } from '../../../../../static/js/jsonrpc'
import { exportButtons } from '../../../../../static/js/datatables_common'

export function drawTable (query = {}) {
    $('.js-spinner').show()
    jsonRPC('Testing.metrics', query, function (response) {
        $('.js-spinner').hide()

        const data = response.results
        const statuses = response.statuses

        const $checkboxes = $('#metrics-coverage-checkboxes')
        $checkboxes.empty()
        statuses.forEach(status => {
            const id = `coverage-status-${status}`
            $checkboxes.append(` <label style="margin-right:12px;"><input type="checkbox" class="coverage-status-checkbox" id="${id}" value="${status}" checked> ${status}</label> `)
        })

        function calculateAndShowExecutionCoverage () {
            const selectedStatuses = []
            $('.coverage-status-checkbox:checked').each(function () {
                selectedStatuses.push($(this).val())
            })

            let totalPlanned = 0
            let totalExecuted = 0
            data.forEach(row => {
                totalPlanned += row.total_planned_cases

                const percentSum = selectedStatuses.reduce((acc, status) => acc + (row[`${status.toLowerCase()}_percent`] || 0), 0)
                const filteredExecuted = Math.round(row.executed_cases * (percentSum / 100))
                totalExecuted += filteredExecuted
            })

            console.log('totalPlanned:', totalPlanned, 'totalExecuted:', totalExecuted)
            const relevantStatuses = selectedStatuses.join(', ')
            const text = `Test Execution Coverage = (Total number of executed test cases or scripts / Total number of test cases or scripts planned to be executed) x 100. A test case is considered executed if at least one of its executions has a relevant status (${relevantStatuses}).`
            $('#metrics-execution-coverage').text(text)
        }

        $('#metrics-help-block-server').show()
        calculateAndShowExecutionCoverage()
        $('.coverage-status-checkbox').on('change', calculateAndShowExecutionCoverage)

        const statusFormulas = statuses.map(status => `Test Coverage for status ${status.toUpperCase()} = (Number of tests with status ${status.toUpperCase()} / Total number of executed tests) × 100`)
        const nota = 'Statuses are dynamically retrieved from the database and may vary depending on system configuration.'
        $('#metrics-nota').text(nota)
        const $list = $('#metrics-status-formulas-list')
        $list.empty()
        statusFormulas.forEach(function (f) {
            $list.append($('<li>').text(f))
        })

        function getSelectedStatuses () {
            const selectedStatuses = []
            $('.coverage-status-checkbox:checked').each(function () {
                selectedStatuses.push($(this).val())
            })
            return selectedStatuses
        }

        function calculateRowCoverage (row, selectedStatuses) {
            if (!row.executed_cases) return '0.00'
            const percentSum = selectedStatuses.reduce((acc, status) => acc + (row[`${status.toLowerCase()}_percent`] || 0), 0)
            const filteredExecuted = Math.round(row.executed_cases * (percentSum / 100))
            return (row.executed_cases ? (filteredExecuted / row.executed_cases * 100).toFixed(2) : '0.00')
        }

        const columns = [
            {
                data: 'test_run_id',
                render: function (data, type, full, meta) {
                    return `<a href="/runs/${data}/">TR-${data}</a>`
                }
            },
            {
                data: 'test_run_name',
                render: function (data, type, full, meta) {
                    return `<a href="/runs/${full.test_run_id}/">${data}</a>`
                }
            },
            { data: 'start_date', title: 'Start Date' },
            { data: 'stop_date', title: 'Stop Date' },
            { data: 'test_plan_name', title: 'Test Plan Name' },
            { data: 'total_planned_cases', title: 'Planned Cases' },
            { data: 'executed_cases', title: 'Executed Cases' }
        ]

        statuses.forEach(status => {
            columns.push({
                data: `${status.toLowerCase()}_percent`,
                title: `${status} (%)`
            })
        })

        columns.push({
            data: null,
            title: 'Execution Coverage (%)',
            render: function (data, type, row, meta) {
                const selectedStatuses = getSelectedStatuses()
                return calculateRowCoverage(row, selectedStatuses)
            },
            className: 'execution-coverage-col'
        })

        let theadHtml = `
            <th>Test Run ID</th>
            <th>Test Run Name</th>
            <th>Start Date</th>
            <th>Stop Date</th>
            <th>Test Plan Name</th>
            <th>Planned Cases</th>
            <th>Executed Cases</th>
        `
        statuses.forEach(status => {
            theadHtml += `<th>${status} (%)</th>`
        })
        theadHtml += '<th>Execution Coverage (%)</th>'
        $('#resultsTableHead').html(theadHtml)

        const dt = $('#resultsTable').DataTable({
            destroy: true,
            pageLength: $('#navbar').data('defaultpagesize'),
            paging: true,
            pagingType: 'bootstrap_input',
            data,
            select: {
                className: 'success',
                style: 'multi',
                selector: 'td > input'
            },
            columns,
            dom: 'Bptp',
            buttons: exportButtons,
            language: {
                loadingRecords: '<div class="spinner spinner-lg"></div>',
                emptyTable: 'No records found.',
                processing: '<div class="spinner spinner-lg"></div>',
                zeroRecords: 'No records found',
                paginate: {
                    previous: 'Previous',
                    next: 'Next',
                    first: 'First',
                    last: 'Last'
                }
            },
            order: [[2, 'desc']]
        })

        $('.coverage-status-checkbox').on('change', function () {
            dt.rows().invalidate().draw(false)
            calcularYMostrarExecutionCoverage()
        })
    })
}

$(document).ready(function () {
    drawTable()

    $(document).on('change', '#id_product, #id_version, #id_build, #id_test_plan', function () {
        searchWithFilters()
    })
    $(document).on('input', '#id_test_run_summary', function () {
        searchWithFilters()
    })
    $(document).on('change', '#id_after, #id_before', function () {
        searchWithFilters()
    })
})

function searchWithFilters () {
    const query = {}
    const products = $('#id_product').val()
    if (products && products.length > 0) query.plan__product__in = products
    const versions = $('#id_version').val()
    if (versions && versions.length > 0) query.plan__product_version__in = versions
    const builds = $('#id_build').val()
    if (builds && builds.length > 0) query.build__in = builds
    const testPlans = $('#id_test_plan').val()
    if (testPlans && testPlans.length > 0) query.plan__in = testPlans
    const after = $('#id_after').val()
    if (after) query.start_date__gte = after
    const before = $('#id_before').val()
    if (before) query.start_date__lte = before
    const summary = $('#id_test_run_summary').val()
    if (summary) query.summary__icontains = summary

    drawTable(query)
}
