import { initializeDateTimePicker } from '../../../../static/js/datetime_picker'
import {
    discoverNestedTestPlans,
    updateBuildSelectFromVersion,
    updateVersionSelectFromProduct,
    updateTestPlanSelectFromProduct
} from '../../../../static/js/utils'
import { loadInitialProduct } from './testing/utils'
import {
    reloadCharts as testingBreakdownDrawChart,
    initializePage as testingBreakdownInitialize
} from './testing/breakdown'
import {
    drawTable as statusMatrixDrawChart,
    initializePage as statusMatrixInitialize
} from './testing/status-matrix'
import { drawTable as executionDashboardDrawTable } from './testing/execution-dashboard'
import { drawChart as executionTrendsDrawChart } from './testing/execution-trends'
import {
    reloadTable as testCaseHealthDrawChart,
    initializePage as testCaseHealthInitialize
} from './testing/test-case-health'

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
        'page-telemetry-execution-dashboard': () => {},
        'page-telemetry-execution-trends': () => {},
        'page-telemetry-test-case-health': testCaseHealthInitialize
    }[pageId]

    initializePage()

    loadInitialProduct()

    document.getElementById('id_product').onchange = () => {
        updateVersionSelectFromProduct('#id_product', '#id_version')
        updateTestPlanSelectFromProduct({ parent: null }, discoverNestedTestPlans)
    }

    document.getElementById('id_version').onchange = () => {
        updateBuildSelectFromVersion(true)
    }

    document.getElementById('btn_search').onclick = drawChart

    drawChart()
}
