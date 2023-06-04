import { initializeDateTimePicker } from '../../../../static/js/datetime_picker'
import {
    updateBuildSelectFromVersion,
    updateVersionSelectFromProduct,
    updateTestPlanSelectFromProduct
} from '../../../../static/js/utils'
import {
    discoverNestedTestPlans
} from '../../../../testcases/static/testcases/js/search'
import { loadInitialProduct } from './testing/utils'
import {
    reloadCharts as testingBreakdownDrawChart,
    initializePage as testingBreakdownInitialize
} from './testing/breakdown'
import {
    drawTable as statusMatrixDrawChart,
    initializePage as statusMatrixInitialize
} from './testing/status-matrix'
import {
    drawTable as executionDashboardDrawTable,
    initializePage as executionDashboardInitialize
} from './testing/execution-dashboard'
import { drawChart as executionTrendsDrawChart } from './testing/execution-trends'
import {
    reloadTable as testCaseHealthDrawChart,
    initializePage as testCaseHealthInitialize
} from './testing/test-case-health'

function delayedHandler (handlerFunc, microSeconds = 1000) {
    let timer = null

    return function () {
        const context = this; const args = arguments
        clearTimeout(timer)
        timer = window.setTimeout(function () {
            handlerFunc.apply(context, args)
        },
        microSeconds)
    }
}

export function pageTelemetryReadyHandler (pageId) {
    initializeDateTimePicker('#id_before')
    initializeDateTimePicker('#id_after')

    const drawChart = {
        'page-telemetry-testing-breakdown': testingBreakdownDrawChart,
        'page-telemetry-status-matrix': statusMatrixDrawChart,
        'page-telemetry-execution-dashboard': executionDashboardDrawTable,
        'page-telemetry-execution-trends': executionTrendsDrawChart,
        'page-telemetry-test-case-health': testCaseHealthDrawChart
    }[pageId]

    const initializePage = {
        'page-telemetry-testing-breakdown': testingBreakdownInitialize,
        'page-telemetry-status-matrix': statusMatrixInitialize,
        'page-telemetry-execution-dashboard': executionDashboardInitialize,
        'page-telemetry-execution-trends': () => {},
        'page-telemetry-test-case-health': testCaseHealthInitialize
    }[pageId]

    initializePage()

    loadInitialProduct()

    document.getElementById('id_product').onchange = () => {
        updateVersionSelectFromProduct()
        // note: don't pass drawChart as callback to avoid calling it twice
        // b/c update_version_select... triggers .onchange()
        updateTestPlanSelectFromProduct({ parent: null }, discoverNestedTestPlans)
    }

    document.getElementById('id_version').onchange = () => {
        drawChart()
        updateBuildSelectFromVersion(true)
    }
    document.getElementById('id_build').onchange = drawChart
    document.getElementById('id_test_plan').onchange = drawChart
    $('#id_test_run_summary').on('keyup', delayedHandler(drawChart))

    $('#id_after').on('dp.change', drawChart)
    $('#id_before').on('dp.change', drawChart)

    drawChart()

    // Close multiselect list when selecting an item
    // Iterate over all dropdown lists
    $('select[multiple]').each(function () {
        $(this).on('change', function () {
            $(this).parent('.bootstrap-select').removeClass('open')
        })
    })
}
