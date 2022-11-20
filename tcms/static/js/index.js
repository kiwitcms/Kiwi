import { pageBugsGetReadyHandler } from '../../bugs/static/bugs/js/get'
import { pageBugsMutableReadyHandler } from '../../bugs/static/bugs/js/mutable'
import { pageBugsSearchReadyHandler } from '../../bugs/static/bugs/js/search'

import { pageTestcasesCloneReadyHandler } from '../../testcases/static/testcases/js/clone'
import { pageTestcasesGetReadyHandler } from '../../testcases/static/testcases/js/get'
import { pageTestcasesMutableReadyHandler } from '../../testcases/static/testcases/js/mutable'
import { pageTestcasesSearchReadyHandler } from '../../testcases/static/testcases/js/search'

const pageHandlers = {
    'page-bugs-get': pageBugsGetReadyHandler,
    'page-bugs-mutable': pageBugsMutableReadyHandler,
    'page-bugs-search': pageBugsSearchReadyHandler,
    'page-testcases-clone': pageTestcasesCloneReadyHandler,
    'page-testcases-get': pageTestcasesGetReadyHandler,
    'page-testcases-mutable': pageTestcasesMutableReadyHandler,
    'page-testcases-search': pageTestcasesSearchReadyHandler
}

$(() => {
    const pageId = $('body').attr('id')
    const readyFunc = pageHandlers[pageId]
    if (readyFunc) {
        readyFunc()
    }

    // todo: add selectpicker() and bootstrapSwitch()
    // initialization here
})
