// JSON-RPC client inspired by
// https://stackoverflow.com/questions/8147211/jquery-jsonrpc-2-0-call-via-ajax-gets-correct-response-but-does-not-work
export function jsonRPC (rpcMethod, rpcParams, callback, isSync, errorCallback) {
    // .filter() args are passed as dictionary but other args,
    // e.g. for .add_tag() are passed as a list of positional values
    if (!Array.isArray(rpcParams)) {
        rpcParams = [rpcParams]
    }

    $.ajax({
        url: '/json-rpc/',
        async: isSync !== true,
        data: JSON.stringify({
            jsonrpc: '2.0',
            method: rpcMethod,
            params: rpcParams,
            id: 'jsonrpc'
        }), // id is needed !!
        // see "Request object" at https://www.jsonrpc.org/specification
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        success: function (result) {
            if (result.error) {
                if (errorCallback) {
                    errorCallback(result.error.message)
                } else {
                    alert(result.error.message)
                }
            } else {
                callback(result.result)
            }
        },
        error: function (err, status, thrown) {
            console.log('*** jsonRPC ERROR: ' + err + ' STATUS: ' + status + ' ' + thrown)

            if (errorCallback) {
                errorCallback(thrown || status)
            }
        }
    })
}

// used by DataTables to convert a list of objects to a dict
// suitable for loading data into the table
export function dataTableJsonRPC (rpcMethod, rpcParams, callbackF, preProcessData) {
    const internalCallback = function (data) {
    // used to collect additional information about columns via ForeignKeys
        if (preProcessData !== undefined) {
            preProcessData(data, callbackF)
        } else {
            callbackF({ data })
        }
    }

    jsonRPC(rpcMethod, rpcParams, internalCallback)
}

export function testPlanAutoComplete (selector, planCache) {
    $(`${selector}.typeahead`).typeahead({
        minLength: 1,
        highlight: true
    }, {
        name: 'plans-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function (element) {
            const displayName = 'TP-' + element.id + ': ' + element.name
            planCache[displayName] = element
            return displayName
        },
        source: function (query, processSync, processAsync) {
            // accepts "TP-1234" or "tp-1234" or "1234"
            query = query.toLowerCase().replace('tp-', '')
            if (query === '') {
                return
            }

            let rpcQuery = { pk: query }

            // or arbitrary string
            if (isNaN(query)) {
                if (query.length >= 3) {
                    rpcQuery = { name__icontains: query }
                } else {
                    return
                }
            }

            jsonRPC('TestPlan.filter', rpcQuery, function (data) {
                return processAsync(data)
            })
        }
    })
}

export function testCaseSummaryAutoComplete (selector) {
    function openTestCase ($suggestion) {
        const suggestion = $suggestion.data('tt-selectable-object')
        window.open(`/case/${suggestion.id}/`, '_blank')
        input.typeahead('close')
    }

    const input = $(`${selector}.typeahead`)
    if (input.length === 0) {
        return
    }

    // remember exactly what the user typed so that navigating the suggestions
    // with the keyboard never replaces it
    let typed = input.val() || ''
    input.on('input', function () {
        typed = this.value
    }).on('keydown', function (event) {
        // Enter opens the highlighted suggestion instead of submitting the form
        if (event.key !== 'Enter') {
            return
        }

        const active = wrapper.find('.tt-suggestion.tt-cursor').first()
        if (active.length) {
            event.preventDefault()
            openTestCase(active)
        }
    }).typeahead({
        minLength: 3,
        highlight: true
    }, {
        name: 'testcase-summaries-autocomplete',
        limit: 10,
        async: true,
        display: function (element) {
            return `TC-${element.id}: ${element.summary}`
        },
        source: function (query, processSync, processAsync) {
            jsonRPC('TestCase.filter', { summary__icontains: query }, function (data) {
                return processAsync(data)
            })
        }
    }).on('typeahead:beforeselect', function (event) {
        // selecting a suggestion must not replace the typed summary
        event.preventDefault()
    }).on('typeahead:beforeautocomplete', function (event) {
        // Tab or the right-arrow key must not insert a suggestion
        event.preventDefault()
    }).on('typeahead:cursorchange', function () {
        // Up/Down move the highlight but keep the typed summary
        $(this).val(typed)
    })

    // override the default inline-block style
    const wrapper = input.closest('span.twitter-typeahead')
    wrapper.css('display', 'block')
    wrapper.find('.tt-menu').css('width', '100%')

    // clicking a suggestion opens the existing test case in a new window
    wrapper.on('click', '.tt-suggestion', function () {
        openTestCase($(this))
    })

    // clicking outside of the input & dropdown closes the menu
    $(document).on('click', function (event) {
        if (!wrapper.is(event.target) && wrapper.has(event.target).length === 0) {
            input.typeahead('close')
        }
    })
}
