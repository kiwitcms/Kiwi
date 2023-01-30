import { pageBugsGetReadyHandler } from '../../bugs/static/bugs/js/get'
import { pageBugsMutableReadyHandler } from '../../bugs/static/bugs/js/mutable'
import { pageBugsSearchReadyHandler } from '../../bugs/static/bugs/js/search'

import { pageTestcasesGetReadyHandler } from '../../testcases/static/testcases/js/get'
import { pageTestcasesMutableReadyHandler } from '../../testcases/static/testcases/js/mutable'
import { pageTestcasesSearchReadyHandler } from '../../testcases/static/testcases/js/search'

import { pageTestplansGetReadyHandler } from '../../testplans/static/testplans/js/get'
import { pageTestplansMutableReadyHandler } from '../../testplans/static/testplans/js/mutable'
import { pageTestplansSearchReadyHandler } from '../../testplans/static/testplans/js/search'

import { pageTestrunsEnvironmentReadyHandler } from '../../testruns/static/testruns/js/environment'
import { pageTestrunsGetReadyHandler } from '../../testruns/static/testruns/js/get'
import { pageTestrunsMutableReadyHandler } from '../../testruns/static/testruns/js/mutable'
import { pageTestrunsSearchReadyHandler } from '../../testruns/static/testruns/js/search'

import { pageManagementBuildAdminReadyHandler } from '../../management/static/management/js/build_admin'

import { pageTelemetryReadyHandler } from '../../telemetry/static/telemetry/js/index'

import { jsonRPC } from './jsonrpc'
import { initSimpleMDE } from './simplemde_security_override'

const pageHandlers = {
    'page-bugs-get': pageBugsGetReadyHandler,
    'page-bugs-mutable': pageBugsMutableReadyHandler,
    'page-bugs-search': pageBugsSearchReadyHandler,

    'page-testcases-get': pageTestcasesGetReadyHandler,
    'page-testcases-mutable': pageTestcasesMutableReadyHandler,
    'page-testcases-search': pageTestcasesSearchReadyHandler,

    'page-testplans-get': pageTestplansGetReadyHandler,
    'page-testplans-mutable': pageTestplansMutableReadyHandler,
    'page-testplans-search': pageTestplansSearchReadyHandler,

    'page-testruns-environment': pageTestrunsEnvironmentReadyHandler,
    'page-testruns-get': pageTestrunsGetReadyHandler,
    'page-testruns-mutable': pageTestrunsMutableReadyHandler,
    'page-testruns-search': pageTestrunsSearchReadyHandler,

    'page-telemetry-testing-breakdown': pageTelemetryReadyHandler,
    'page-telemetry-status-matrix': pageTelemetryReadyHandler,
    'page-telemetry-execution-trends': pageTelemetryReadyHandler,
    'page-telemetry-test-case-health': pageTelemetryReadyHandler
}

$(() => {
    const body = $('body')
    const pageId = body.attr('id')
    const readyFunc = pageHandlers[pageId]
    if (readyFunc) {
        readyFunc(pageId)
    }

    // this page doesn't have a page id
    if (body.hasClass('grp-change-form') && body.hasClass('management-build')) {
        pageManagementBuildAdminReadyHandler()
    }

    if ($('body').selectpicker) {
        $('.selectpicker').selectpicker()
    }

    if ($('body').bootstrapSwitch) {
        $('.bootstrap-switch').bootstrapSwitch()
    }

    if ($('body').tooltip) {
        $('[data-toggle="tooltip"]').tooltip()
    }

    // used by automatically loaded editor widgets
    window.initSimpleMDE = initSimpleMDE

    // for debugging in browser
    window.jsonRPC = jsonRPC
})
