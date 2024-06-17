// JSON-RPC client inspired by
// https://stackoverflow.com/questions/8147211/jquery-jsonrpc-2-0-call-via-ajax-gets-correct-response-but-does-not-work
export function jsonRPC (rpcMethod, rpcParams, callback, isSync) {
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
                alert(result.error.message)
            } else {
                callback(result.result)
            }
        },
        error: function (err, status, thrown) {
            console.log('*** jsonRPC ERROR: ' + err + ' STATUS: ' + status + ' ' + thrown)
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
