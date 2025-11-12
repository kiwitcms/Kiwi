import { dataTableJsonRPC, jsonRPC } from '../../../../../static/js/jsonrpc'
import { exportButtons } from '../../../../../static/js/datatables_common'
import { escapeHTML } from '../../../../../static/js/utils'

export function initializePage () {
    document.getElementById('id_include_child_tps').onchange = drawTable
}

function preProcessData (data, callbackF) {
    const caseDict = {}
    const runDict = {}
    data.forEach(function (element) {
        caseDict[element.case] = true
        runDict[element.run] = true
    })
    // remove duplicate IDs to minimize the size of WHERE clause
    const caseIds = Object.keys(caseDict).map(id => parseInt(id))
    const runIds = Object.keys(runDict).map(id => parseInt(id))

    jsonRPC('TestCase.filter', { pk__in: caseIds }, function (cases) {
        const testerPerCase = {}
        const componentsPerCase = {}
        const priorityPerCase = {}
        const automatedPerCase = {}
        cases.forEach(function (element) {
            testerPerCase[element.id] = element.default_tester__username
            priorityPerCase[element.id] = element.priority__value
            automatedPerCase[element.id] = element.is_automated
        })

        jsonRPC('Component.filter', { cases__in: caseIds }, function (components) {
            components.forEach(function (component) {
                if (componentsPerCase[component.cases] === undefined) {
                    componentsPerCase[component.cases] = []
                }
                componentsPerCase[component.cases].push(component.name)
            })

            jsonRPC('TestRun.filter', { pk__in: runIds }, function (runs) {
                const productDict = {}
                runs.forEach(function (run) {
                    productDict[run.build__version__product] = true
                })
                const productIds = Object.keys(productDict).map(id => parseInt(id))

                jsonRPC('Product.filter', { pk__in: productIds }, function (products) {
                    const productPerRun = {}
                    const productNames = {}
                    const testerPerRun = {}
                    products.forEach(function (product) {
                        productNames[product.id] = product.name
                    })
                    runs.forEach(function (run) {
                        testerPerRun[run.id] = run.default_tester__username
                        productPerRun[run.id] = productNames[run.build__version__product]
                    })

                    // augment data set with additional info
                    data.forEach(function (element) {
                        element.default_tester__from_case = testerPerCase[element.case]
                        element.default_tester__from_run = testerPerRun[element.run]
                        element.product__name = productPerRun[element.run]
                        element.test_case_components = (componentsPerCase[element.case] ?? []).join(', ')
                        element.case__priority = priorityPerCase[element.case]
                        element.case__automated = automatedPerCase[element.case]
                    })

                    callbackF({ data }) // renders everything
                })
            })
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

            // if page has URI params then try filtering, e.g. by run_id
            const filterParams = new URLSearchParams(location.search)
            if (filterParams.has('run_id')) {
                query.run__in = filterParams.getAll('run_id')
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
                    return `<a href="/case/${data.case}/">TC-${data.case}: ` + escapeHTML(data.case__summary) + '</a>'
                }
            },
            {
                data: 'case__priority'
            },
            {
                data: 'case__automated'
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
                data: 'product__name'
            },
            {
                data: 'build__name'
            },
            {
                data: 'test_case_components'
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
        dom: 'Biptip',
        buttons: exportButtons,
        language: {
            info: $('#main-element').data('trans-x-records-found'),
            infoEmpty: $('#main-element').data('trans-no-records-found'),
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            thousands: '',
            zeroRecords: $('#main-element').data('trans-no-records-found')
        },
        order: [[1, 'asc']]
    })
}
