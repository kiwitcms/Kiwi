function loadInitialProduct (callback = () => {}) {
    jsonRPC('Product.filter', {}, data => {
        updateSelect(data, '#id_product', 'id', 'name', null)
        callback()
    })
}

function showOnlyRoundNumbers (number) {
    return number % 1 === 0 ? number : ''
}

// we need this function, because the standard library does not have
// one that rounds the number down, which means that the sum
// of the percents may become more than 100% and that breaksg the chart
function roundDown (number) {
    return Math.floor(number * 100) / 100
}

const whenReady = {
    'page-telemetry-testing-breakdown': () => {
        function reloadCharts () {
            const query = {}

            const testPlanIds = $('#id_test_plan').val()
            const productIds = $('#id_product').val()

            if (testPlanIds.length) {
                query.plan__in = testPlanIds
            } else if (productIds.length) {
                query.category__product_id__in = productIds
            }

            const dateBefore = $('#id_before')
            if (dateBefore.val()) {
                query.create_date__lte = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
            }

            const dateAfter = $('#id_after')
            if (dateAfter.val()) {
                query.create_date__gte = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
            }

            jsonRPC('Testing.breakdown', query, result => {
                drawAutomatedBar(result.count)
                drawPrioritiesChart(result.priorities)
                drawCategoriesChart(result.categories)
            }, true)
        }

        function drawAutomatedBar (count) {
            d3.select('#total-count')
                .style('font-weight', 'bold')
                .style('font-size', '18px')
                .text(count.all)

            d3.selectAll('.progress-bar')
                .attr('aria-valuemin', '0')
                .attr('aria-valuemax', '100')

            d3.select('.automated-legend-text > span').remove()
            d3.select('.manual-legend-text > span').remove()

            d3.select('.automated-legend-text')
                .append('span')
                .text(` - ${count.automated}`)

            d3.select('.manual-legend-text')
                .append('span')
                .text(` - ${count.manual}`)

            const automatedPercent = count.automated / count.all * 100

            d3.select('.automated-bar')
                .attr('aria-valuenow', `${automatedPercent}`)
                .attr('title', `${count.automated} Automated`)
                .style('width', `${automatedPercent}%`)

            const manualPercent = count.manual / count.all * 100

            d3.select('.manual-bar')
                .attr('aria-valuenow', `${manualPercent}`)
                .attr('title', `${count.manual} Manual`)
                .style('width', `${manualPercent}%`)
        }

        function drawPrioritiesChart (priorities) {
            drawChart(priorities, 'priority', '#priorities-chart')
        }

        function drawCategoriesChart (categories) {
            drawChart(categories, 'category', '#categories-chart')
        }

        function drawChart (data, type, selector) {
            const categories = new Set()
            const groups = [[]]
            const chartData = []

            Object.values(data).forEach(entry => {
                Object.keys(entry).forEach(key => categories.add(key))
            })

            Object.entries(data).forEach(entry => {
                const group = entry[0]
                groups[0].push(group)

                const dataEntry = [group]

                categories.forEach(cat => {
                    let count = entry[1][cat]
                    if (!count) {
                        count = 0
                    }
                    dataEntry.push(count)
                })

                chartData.push(dataEntry)
            })

            const chartConfig = $().c3ChartDefaults().getDefaultStackedBarConfig()
            chartConfig.bindto = selector
            chartConfig.axis = {
                x: {
                    categories: Array.from(categories),
                    type: 'category'
                },
                y: {
                    tick: {
                        format: showOnlyRoundNumbers
                    }
                }
            }
            chartConfig.data = {
                columns: chartData,
                groups,
                type: 'bar',
                order: null
            }
            chartConfig.color = {
                pattern: [
                    $.pfPaletteColors.blue,
                    $.pfPaletteColors.red100
                ]
            }
            chartConfig.grid = {
                show: false
            }

            c3.generate(chartConfig)
        }

        loadInitialProduct(reloadCharts)

        $('#id_after').on('dp.change', reloadCharts)
        $('#id_before').on('dp.change', reloadCharts)
        document.getElementById('id_test_plan').onchange = reloadCharts
        document.getElementById('id_product').onchange = () => {
            updateTestPlanSelectFromProduct(reloadCharts)
        }

        // not relevant in this context
        $('#version_and_build').hide()
    },

    'page-telemetry-test-case-health': () => {
        function renderTestCaseColumn (data) {
            return `<a href="/case/${data.case_id}">TC-${data.case_id}</a>: ${data.case_summary}`
        }

        function renderFailedExecutionsColumn (data) {
            return `${data.count.fail} / ${data.count.all}`
        }

        function renderPercentColumn (data) {
            return Number.parseFloat(data.count.fail / data.count.all * 100).toFixed(1)
        }

        function renderVisualPercent (data) {
            const failPercent = data.count.fail / data.count.all * 100

            const colors = []
            const step = 20
            for (i = 0; i < 5; i++) {
                if (failPercent > i * step) {
                    colors.push('#cc0000') // pf-red-100
                } else {
                    colors.push('#3f9c35') // pf-green-400
                }
            }

            return colors.reduce((prev, color) => prev + `<span class='visual-percent-box' style='background-color: ${color}'></span>\n`, '')
        }

        loadInitialProduct()

        const table = $('#test-case-health-table').DataTable({
            ajax: function (data, callback, settings) {
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
                if (testPlanIds.length) {
                    query.run__plan__in = testPlanIds
                }

                const dateBefore = $('#id_before')
                if (dateBefore.val()) {
                    query.stop_date__lte = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
                }

                const dateAfter = $('#id_after')
                if (dateAfter.val()) {
                    query.stop_date__gte = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
                }

                dataTableJsonRPC('Testing.test_case_health', query, callback)
            },
            columns: [
                {
                    data: null,
                    render: renderTestCaseColumn
                },
                {
                    data: null,
                    render: renderVisualPercent
                },
                {
                    data: null,
                    render: renderFailedExecutionsColumn
                },
                {
                    data: null,
                    render: renderPercentColumn
                }
            ],
            paging: false,
            ordering: false,
            dom: 't',
            language: {
                loadingRecords: '<div class="spinner spinner-lg"></div>',
                processing: '<div class="spinner spinner-lg"></div>',
                zeroRecords: 'No records found'
            }
        })

        document.getElementById('id_product').onchange = () => {
            updateVersionSelectFromProduct()
            // note: don't call table.ajax.reload() here to avoid calling it twice
            // b/c update_version_select... triggers .onchange()
            updateTestPlanSelectFromProduct()
        }

        document.getElementById('id_version').onchange = () => {
            updateBuildSelectFromVersion(true)
            table.ajax.reload()
        }

        document.getElementById('id_build').onchange = () => {
            table.ajax.reload()
        }
        document.getElementById('id_test_plan').onchange = () => {
            table.ajax.reload()
        }

        $('#id_after').on('dp.change', () => {
            table.ajax.reload()
        })
        $('#id_before').on('dp.change', () => {
            table.ajax.reload()
        })
    },

    'page-telemetry-execution-trends': () => {
        function drawChart () {
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
            if (testPlanIds.length) {
                query.run__plan__in = testPlanIds
            }

            const dateBefore = $('#id_before')
            if (dateBefore.val()) {
                query.stop_date__lte = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
            }

            const dateAfter = $('#id_after')
            if (dateAfter.val()) {
                query.stop_date__gte = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
            }

            const totalKey = $('.main').data('total-key')

            jsonRPC('Testing.execution_trends', query, data => {
                drawPassingRateSummary(data.status_count)

                const chartData = Object.entries(data.data_set).map(entry => [entry[0], ...entry[1]])
                const categories = data.categories.map(testRunId => `TR-${testRunId}`)

                $('#chart > svg').remove()

                const c3ChartDefaults = $().c3ChartDefaults()
                const config = c3ChartDefaults.getDefaultAreaConfig()
                config.axis = {
                    x: {
                        categories,
                        type: 'category',
                        tick: {
                            fit: false,
                            multiline: false
                        }
                    },
                    y: {
                        tick: {
                            format: showOnlyRoundNumbers
                        }
                    }
                }
                config.bindto = '#chart'
                config.color = {
                    pattern: data.colors
                }
                config.data = {
                    columns: chartData,
                    type: 'area-spline',
                    order: null
                }
                config.bar = {
                    width: {
                        ratio: 1
                    }
                }
                config.tooltip = {
                    format: {
                        value: (value, _ratio, _id, _index) => value || undefined
                    }
                }
                config.legend = {
                    hide: [totalKey]
                }
                c3.generate(config)

                // hide the total data point
                $(`.c3-target-${totalKey}`).addClass('hidden')
            })
        }

        function drawPassingRateSummary (statusCount) {
            const allCount = statusCount.positive + statusCount.negative + statusCount.neutral
            $('.passing-rate-summary .total').text(allCount)

            const positivePercent = statusCount.positive ? roundDown(statusCount.positive / allCount * 100) : 0
            const positiveBar = $('.progress > .progress-bar-success')
            const positiveRateText = `${positivePercent}%`
            positiveBar.css('width', positiveRateText)
            positiveBar.text(positiveRateText)
            $('.passing-rate-summary .positive').text(statusCount.positive)

            const neutralPercent = statusCount.neutral ? roundDown(statusCount.neutral / allCount * 100) : 0
            const neutralRateText = `${neutralPercent}%`
            const neutralBar = $('.progress > .progress-bar-remaining')
            neutralBar.css('width', neutralRateText)
            neutralBar.text(neutralRateText)
            $('.passing-rate-summary .neutral').text(statusCount.neutral)

            const negativePercent = statusCount.negative ? roundDown(statusCount.negative / allCount * 100) : 0
            const negativeRateText = `${negativePercent}%`
            const negativeBar = $('.progress > .progress-bar-danger')
            negativeBar.css('width', negativeRateText)
            negativeBar.text(negativeRateText)
            $('.passing-rate-summary .negative').text(statusCount.negative)
        }

        loadInitialProduct()

        document.getElementById('id_product').onchange = () => {
            updateVersionSelectFromProduct()
            // note: don't pass drawChart as callback to avoid calling it twice
            // b/c update_version_select... triggers .onchange()
            updateTestPlanSelectFromProduct()
        }

        document.getElementById('id_version').onchange = () => {
            drawChart()
            updateBuildSelectFromVersion(true)
        }
        document.getElementById('id_build').onchange = drawChart
        document.getElementById('id_test_plan').onchange = drawChart

        $('#id_after').on('dp.change', drawChart)
        $('#id_before').on('dp.change', drawChart)

        drawChart()
    },

    'page-telemetry-status-matrix': () => {
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

        function setMaxHeight (t) {
            const maxH = 0.99 * (window.innerHeight - t.position().top)
            t.css('max-height', maxH)
        }

        function drawTable () {
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
                        color = el.attributes.color.nodeValue
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

        loadInitialProduct()

        document.getElementById('id_product').onchange = () => {
            updateVersionSelectFromProduct()
            // note: don't pass drawTable as callback to avoid calling it twice
            // b/c update_version_select... triggers .onchange()
            updateTestPlanSelectFromProduct()
        }

        document.getElementById('id_version').onchange = () => {
            drawTable()
            updateBuildSelectFromVersion(true)
        }

        document.getElementById('id_build').onchange = drawTable
        document.getElementById('id_test_plan').onchange = drawTable
        document.getElementById('id_order').onchange = drawTable
        document.getElementById('id_include_child_tps').onchange = drawTable

        $('#id_after').on('dp.change', drawTable)
        $('#id_before').on('dp.change', drawTable)

        drawTable()

        $('#table').on('draw.dt', function () {
            setMaxHeight($(this))
        })

        $(window).on('resize', function () {
            setMaxHeight($('#table'))
        })
    }

}

$(() => {
    const pageId = $('body').attr('id')
    const readyFunc = whenReady[pageId]
    if (readyFunc) {
        readyFunc()
    }

    // Close multiselect list when selecting an item
    // Iterate over all dropdown lists
    $('select[multiple]').each(function () {
        $(this).on('change', function () {
            $(this).parent('.bootstrap-select').removeClass('open')
        })
    })

    $('.bootstrap-switch').bootstrapSwitch()
    $('.selectpicker').selectpicker()

    // TODO: initialization of Telemetry .ready() handlers is very similar,
    // see https://github.com/kiwitcms/Kiwi/issues/1118
})
