import { pageBugsGetReadyHandler } from '../../bugs/static/bugs/js/get'
import { pageBugsMutableReadyHandler } from '../../bugs/static/bugs/js/mutable'
import { pageBugsSearchReadyHandler } from '../../bugs/static/bugs/js/search'

const pageHandlers = {
    'page-bugs-get': pageBugsGetReadyHandler,
    'page-bugs-mutable': pageBugsMutableReadyHandler,
    'page-bugs-search': pageBugsSearchReadyHandler
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
