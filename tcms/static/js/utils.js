import { jsonRPC } from './jsonrpc'

/*
    Used to update a select when something else changes.
*/
export function updateSelect (data, selector, idAttr, valueAttr, groupAttr) {
    const _selectTag = $(selector)[0]
    let newOptions = ''
    let currentGroup = ''
    const isMultiple = _selectTag.attributes.getNamedItem('multiple') !== null

    // in some cases using single select, the 1st <option> element is ---
    // which must always be there to indicate nothing selected
    if (!isMultiple && _selectTag.options.length) {
        newOptions = _selectTag.options[0].outerHTML
    }

    data.forEach(function (element) {
        if (isMultiple && groupAttr != null && currentGroup !== element[groupAttr]) {
            if (currentGroup !== '') {
                // for all but the first time group changes, add a closing optgroup tag
                newOptions += '</optgroup>'
            }
            newOptions += '<optgroup label="' + element[groupAttr] + '">'
            currentGroup = element[groupAttr]
        }

        newOptions += '<option value="' + element[idAttr] + '">' + element[valueAttr] + '</option>'
    })

    // add a final closing optgroup tag if opening tag present
    if (newOptions.indexOf('optgroup') > -1) {
        newOptions += '</optgroup>'
    }

    _selectTag.innerHTML = newOptions

    if ($('body').selectpicker) {
        $(selector).selectpicker('refresh')
    }
}

/*
    Used for on-change event handlers
*/
export function updateVersionSelectFromProduct () {
    const updateVersionSelectCallback = function (data) {
        updateSelect(data, '#id_version', 'id', 'value', 'product__name')

        // trigger on-change handler, possibly updating build
        $('#id_version').change()
    }

    let productIds = $('#id_product').val()

    if (productIds && productIds.length) {
        if (!Array.isArray(productIds)) {
            productIds = [productIds]
        }

        jsonRPC('Version.filter', { product__in: productIds }, updateVersionSelectCallback)
    } else {
        updateVersionSelectCallback([])
    }
}

export function populateVersion () {
    const productId = $('#id_product').val()

    if (productId === null) {
        $('#add_id_version').addClass('disabled')
        $('#add_id_build').addClass('disabled')
    } else {
        $('#add_id_version').removeClass('disabled')
        $('#add_id_build').removeClass('disabled')
    }

    const href = $('#add_id_version')[0].href
    $('#add_id_version')[0].href = href.slice(0, href.indexOf('&product'))
    $('#add_id_version')[0].href += `&product=${productId}`
    $('#id_version').find('option').remove()
    updateVersionSelectFromProduct()
}

/*
    Used for on-change event handlers
*/
export function updateBuildSelectFromVersion (keepFirst) {
    const updateCallback = function (data) {
        updateSelect(data, '#id_build', 'id', 'name', 'version__value')
    }

    if (keepFirst === true) {
    // pass
    } else {
        $('#id_build').find('option').remove()
    }

    let versionIds = $('#id_version').val()
    if (versionIds && versionIds.length) {
        if (!Array.isArray(versionIds)) {
            versionIds = [versionIds]
        }

        jsonRPC('Build.filter', { version__in: versionIds }, updateCallback)
    } else {
        updateCallback([])
    }
}

export function populateBuild () {
    const productId = $('#id_product').val()
    const versionId = $('#id_version').val()

    if (versionId === null) {
        $('#add_id_build').addClass('disabled')
    } else {
        $('#add_id_build').removeClass('disabled')
    }

    const href = $('#add_id_build')[0].href
    $('#add_id_build')[0].href = href.slice(0, href.indexOf('&version'))
    $('#add_id_build')[0].href += `&version=${versionId}&product=${productId}`
    updateBuildSelectFromVersion()
}
/*
    Used for on-change event handlers
*/
export function updateCategorySelectFromProduct () {
    const updateCallback = function (data) {
        updateSelect(data, '#id_category', 'id', 'name')
    }

    const productId = $('#id_product').val()
    if (productId) {
        jsonRPC('Category.filter', { product: productId }, updateCallback)
    } else {
        updateCallback([])
    }
}

/*
    Used for on-change event handlers
*/
export function updateComponentSelectFromProduct () {
    const updateCallback = function (data) {
        data = arrayToDict(data)
        updateSelect(Object.values(data), '#id_component', 'id', 'name')
    }

    const productId = $('#id_product').val()
    if (productId) {
        jsonRPC('Component.filter', { product: productId }, updateCallback)
    } else {
        updateCallback([])
    }
}

/*
    Split the input string by comma and return
    a list of trimmed values
*/
export function splitByComma (input) {
    const result = []

    input.split(',').forEach(function (element) {
        element = element.trim()
        if (element) {
            result.push(element)
        }
    })
    return result
}

/*
    Given a params dictionary and a selector update
    the dictionary so we can search by tags!
    Used in search.js
*/
export function updateParamsToSearchTags (selector, params) {
    const tagList = splitByComma($(selector).val())

    if (tagList.length > 0) {
        params.tag__name__in = tagList
    };
}

/*
    Replaces HTML characters for display in DataTables

    backslash(\), quotes('), double quotes (")
    https://github.com/kiwitcms/Kiwi/issues/78

    angle brackets (<>)
    https://github.com/kiwitcms/Kiwi/issues/234
*/
export function escapeHTML (unsafe) {
    return unsafe.replace(/[&<>"']/g, function (m) {
        return ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            '\'': '&#039;'
        })[m]
    })
}

export function unescapeHTML (html) {
    return html
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#039;/g, '\'')
    // always keep the ampersand escape last
    // to avoid chain unescape of nested values, see
    // https://github.com/kiwitcms/Kiwi/issues/2800
        .replace(/&amp;/g, '&')
}

export function treeViewBind (selector = '.tree-list-view-pf') {
    // collapse all child rows
    $(selector).find('.list-group-item-container').addClass('hidden')

    // unbind previous events b/c this function is now reentrant
    // click the list-view heading then expand a row
    $(selector).find('.list-group-item-header').off('click').click(function (event) {
        if (!$(event.target).is('button, a, input, .fa-ellipsis-v')) {
            const $this = $(this)
            $this.find('.fa-angle-right').toggleClass('fa-angle-down')
            const $itemContainer = $this.siblings('.list-group-item-container')
            if ($itemContainer.children().length) {
                $itemContainer.toggleClass('hidden')
            }
        }
    })
}

export function animate (target, handler, time = 500) {
    target.fadeOut(time, handler).fadeIn(time)
}

export function currentTimeWithTimezone (timeZone) {
    return moment().tz(timeZone).format('YYYY-MM-DD HH:mm:ss')
}

/* render Markdown & assign it to selector */
export function markdown2HTML (input, selector) {
    // first display raw input in case user is not logged in and
    // Markdown.render returns 403 forbidden
    $(selector).html(input)

    jsonRPC('Markdown.render', unescapeHTML(input), function (result) {
        $(selector).html(unescapeHTML(result))
    })
}

export function renderCommentHTML (index, comment, template, bindDeleteFunc) {
    const newNode = $(template.content.cloneNode(true))

    newNode.find('.js-comment-container').attr('data-comment-id', comment.id)
    newNode.find('.index').html(`#${index}`)
    newNode.find('.user').html(comment.user_name)
    newNode.find('.date').html(comment.submit_date)
    markdown2HTML(comment.comment, newNode.find('.comment')[0])

    if (bindDeleteFunc) {
        bindDeleteFunc(newNode)
    }

    return newNode
}

export function bindDeleteCommentButton (objId, deleteMethod, canDelete, parentNode) {
    if (canDelete) {
        parentNode.find('.js-comment-delete-btn').click(function (event) {
            const commentId = $(event.target).parents('.js-comment-container').data('comment-id')
            jsonRPC(deleteMethod, [objId, commentId], function (result) {
                $(event.target).parents('.js-comment-container').hide()
            })

            return false
        })
    } else {
        parentNode.find('.js-comment-delete-btn').hide()
    }
}

export function renderCommentsForObject (objId, getMethod, deleteMethod, canDelete, parentNode) {
    parentNode.empty()
    const commentTemplate = $('template#comment-template')[0]

    jsonRPC(getMethod, [objId], comments => {
        comments.forEach((comment, index) => parentNode.append(renderCommentHTML(index + 1, comment, commentTemplate)))

        bindDeleteCommentButton(objId, deleteMethod, canDelete, parentNode)
    })
}

export function showPopup (href) {
    if (href.indexOf('?') === -1) {
        href += '?nonav=1'
    } else {
        href += '&nonav=1'
    }

    const win = window.open(href, 'popup page', 'width=1024,height=612')
    win.focus()

    return win
}

// used in testplans/get.html and testruns/get.html
// objId - PK of the object we're adding to
// rpcMethod - must accept [pk, case_id] - the method used to do the work
// href - URL of the search page
// errorMessage - message to display in case of RPC errors
export function advancedSearchAndAddTestCases (objId, rpcMethod, href, errorMessage) {
    window.addTestCases = function (testCaseIDs, sender) {
        let rpcErrors = 0

        // close the popup
        sender.close()

        if (testCaseIDs) {
            // monkey-patch the alert() function
            const oldAlert = window.alert
            alert = window.alert = function (message) {
                rpcErrors += 1
            }

            // add the selected test cases
            testCaseIDs.forEach(function (testCase) {
                jsonRPC(rpcMethod, [objId, testCase], function (result) {}, true)
            })

            // revert monkey-patch
            alert = window.alert = oldAlert
        }

        if (rpcErrors) {
            alert(errorMessage)
        }

        // something was added so reload the page
        if (rpcErrors < testCaseIDs.length) {
            window.location.reload(true)
            // TODO: figure out how to reload above and add the new value to the page
        }
    }

    if (href.indexOf('?') === -1) {
        href += '?allow_select=1'
    } else {
        href += '&allow_select=1'
    }

    showPopup(href)

    return false
}

// used in both testplans/get.html and testruns/get.html to initialize and
// handle the quicksearch widget
// objId - PK of the object we're adding to
// pageCallback - function which performs the actual RPC call of adding
//                the selected TC to objId and refreshes the page
// cache - cache of previous values fetched for typeahead
// initialQuery - an initial RPC query that is AND'ed to the internal conditions
//                for example: filter only CONFIRMED TCs.
export function quickSearchAndAddTestCase (objId, pageCallback, cache, initialQuery = {}) {
    // + button
    $('#btn-add-case').click(function () {
        pageCallback(objId)

        return false
    })

    // Enter key
    $('#search-testcase').keyup(function (event) {
        if (event.keyCode === 13) {
            pageCallback(objId)

            return false
        };
    })

    // autocomplete
    $('#search-testcase.typeahead').typeahead({
        minLength: 1,
        highlight: true
    }, {
        name: 'testcases-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function (element) {
            const displayName = `TC-${element.id}: ${element.summary}`
            cache[displayName] = element
            return displayName
        },
        source: function (query, processSync, processAsync) {
            // accepts "TC-1234" or "tc-1234" or "1234"
            query = query.toLowerCase().replace('tc-', '')
            if (query === '') {
                return
            }

            let rpcQuery = { pk: query }

            // or arbitrary string
            if (isNaN(query)) {
                if (query.length >= 3) {
                    rpcQuery = { summary__icontains: query }
                } else {
                    return
                }
            }

            // merge initial query for more filtering if specified
            rpcQuery = Object.assign({}, rpcQuery, initialQuery)

            jsonRPC('TestCase.filter', rpcQuery, function (data) {
                return processAsync(data)
            })
        }
    })
}

// on dropdown change update the label of the button and set new selected list item
export function changeDropdownSelectedItem (dropDownSelector, buttonSelector, target, focusTarget) {
    $(`${buttonSelector}`)[0].innerHTML = target.innerText + '<span class="caret"></span>'

    // remove selected class
    $(`${dropDownSelector} li`).each(function (index, el) {
        el.className = ''
    })

    // target is a tag
    target.parentElement.className = 'selected'

    // close the parent menu
    $(target).parents('.open').toggleClass('open')

    // clear the text & the current filter
    if (focusTarget) {
        focusTarget.val('').keyup().focus()
    }

    // don't follow links
    return false
}

export function arrayToDict (arr) {
    return arr.reduce(function (map, obj) {
        map[obj.id] = obj
        return map
    }, {})
}

export function updateTestPlanSelectFromProduct (
    extraQuery = {},
    preProcessData = (data, callbackF) => { callbackF(data) }
) {
    const internalCallback = function (data = []) {
        preProcessData(data, (data) => {
            updateSelect(data, '#id_test_plan', 'id', 'name', 'product__name')
        })
    }

    let productIds = $('#id_product').val()

    if (productIds === '') {
        internalCallback()
        return
    } else if (!Array.isArray(productIds)) {
        productIds = [productIds]
    }

    if (!productIds.length) {
        internalCallback()
    } else {
        const query = { product__in: productIds }
        Object.assign(query, extraQuery)
        jsonRPC('TestPlan.filter', query, internalCallback)
    }
}
