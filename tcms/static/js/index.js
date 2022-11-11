// JSON-RPC client inspired by
// https://stackoverflow.com/questions/8147211/jquery-jsonrpc-2-0-call-via-ajax-gets-correct-response-but-does-not-work
function jsonRPC (rpcMethod, rpcParams, callback, isSync) {
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
function dataTableJsonRPC (rpcMethod, rpcParams, callback, preProcessData) {
    const internalCallback = function (data) {
    // used to collect additional information about columns via ForeignKeys
        if (preProcessData !== undefined) {
            preProcessData(data, callback)
        } else {
            callback({ data })
        }
    }

    jsonRPC(rpcMethod, rpcParams, internalCallback)
}

/*
    Used to update a select when something else changes.
*/
function updateSelect (data, selector, idAttr, valueAttr, groupAttr) {
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

    try {
        $(selector).selectpicker('refresh')
    } catch (e) {
        console.warn(e)
    }
}

/*
    Used for on-change event handlers
*/
function updateVersionSelectFromProduct () {
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

/*
    Used for on-change event handlers
*/
function updateBuildSelectFromVersion (keepFirst) {
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

/*
    Used for on-change event handlers
*/
function updateCategorySelectFromProduct () {
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
function updateComponentSelectFromProduct () {
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
function splitByComma (input) {
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
function updateParamsToSearchTags (selector, params) {
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
function escapeHTML (unsafe) {
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

function unescapeHTML (html) {
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

function treeViewBind (selector = '.tree-list-view-pf') {
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

const animate = (target, handler, time = 500) => target.fadeOut(time, handler).fadeIn(time)
const currentTimeWithTimezone = timeZone => moment().tz(timeZone).format('YYYY-MM-DD HH:mm:ss')

/* render Markdown & assign it to selector */
function markdown2HTML (input, selector) {
    // first display raw input in case user is not logged in and
    // Markdown.render returns 403 forbidden
    $(selector).html(input)

    jsonRPC('Markdown.render', unescapeHTML(input), function (result) {
        $(selector).html(unescapeHTML(result))
    })
}

function renderCommentHTML (index, comment, template, bindDeleteFunc) {
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

function bindDeleteCommentButton (objId, deleteMethod, canDelete, parentNode) {
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

function renderCommentsForObject (objId, getMethod, deleteMethod, canDelete, parentNode) {
    const commentTemplate = $('template#comment-template')[0]

    jsonRPC(getMethod, [objId], comments => {
        comments.forEach((comment, index) => parentNode.append(renderCommentHTML(index + 1, comment, commentTemplate)))

        bindDeleteCommentButton(objId, deleteMethod, canDelete, parentNode)
    })
}

function showPopup (href) {
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
function advancedSearchAndAddTestCases (objId, rpcMethod, href, errorMessage) {
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
function quickSearchAndAddTestCase (objId, pageCallback, cache, initialQuery = {}) {
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
function changeDropdownSelectedItem (dropDownSelector, buttonSelector, target, focusTarget) {
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

function arrayToDict (arr) {
    return arr.reduce(function (map, obj) {
        map[obj.id] = obj
        return map
    }, {})
}

function updateTestPlanSelectFromProduct (callback = () => {}) {
    const updateCallback = (data = []) => {
        updateSelect(data, '#id_test_plan', 'id', 'name', 'product__name')
        callback()
    }

    let productIds = $('#id_product').val()

    if (productIds === '') {
        updateCallback()
        return
    } else if (!Array.isArray(productIds)) {
        productIds = [productIds]
    }

    if (!productIds.length) {
        updateCallback()
    } else {
        jsonRPC('TestPlan.filter', { product__in: productIds }, updateCallback)
    }
}

/*
    Applies tag to the chosen model

    @model - string - model name which accepts tags. There must
        be a 'MM.add_tag' RPC function for this to work!
    @objectId - int - PK of the object that will be tagged
    @tagInput - jQuery object - usually an <input> element which
        provides the value used for tagging
    @toTable - DataTable object - the table which displays the results
*/
function addTag (model, objectId, tagInput, toTable) {
    const tagName = tagInput.value

    if (tagName.length > 0) {
        jsonRPC(model + '.add_tag', [objectId, tagName], function (data) {
            toTable.row.add({ name: tagName }).draw()
            $(tagInput).val('')
        })
    }
}

/*
    Displays the tags table inside a card and binds all buttons
    and actions for it.

    @model - string - model name which accepts tags. There must
        be a 'MM.add_tag' RPC function for this to work!
    @objectId - int - PK of the object that will be tagged
    @displayFilter - dict - passed directly to `Tag.filter` to display
        tags for @objectId
    @permRemove - bool - if we have permission to remove tags

*/
function tagsCard (model, objectId, displayFilter, permRemove) {
    // load the tags table
    const tagsTable = $('#tags').DataTable({
        ajax: function (data, callback, settings) {
            dataTableJsonRPC('Tag.filter', displayFilter, callback, function (data, callback) {
                // b/c tags are now annotated with case, run, plan IDs there are duplicate names.
                // Filter them out by only looking at Tag.id uniqueness!
                data = arrayToDict(data)
                callback({ data: Object.values(data) })
            })
        },
        columns: [
            { data: 'name' },
            {
                data: null,
                sortable: false,
                render: function (data, type, full, meta) {
                    if (permRemove) {
                        return '<a href="#tags" class="remove-tag" data-name="' + data.name + '"><span class="pficon-error-circle-o hidden-print"></span></a>'
                    }
                    return ''
                }
            }
        ],
        dom: 't',
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: 'No records found'
        },
        order: [[0, 'asc']]
    })

    // remove tags button
    tagsTable.on('draw', function () {
        $('.remove-tag').click(function () {
            const tr = $(this).parents('tr')

            jsonRPC(model + '.remove_tag', [objectId, $(this).data('name')], function (data) {
                tagsTable.row($(tr)).remove().draw()
            })
        })
    })

    // add tag button and Enter key
    $('#add-tag').click(function () {
        addTag(model, objectId, $('#id_tags')[0], tagsTable)
    })

    $('#id_tags').keyup(function (event) {
        if (event.keyCode === 13) {
            addTag(model, objectId, $('#id_tags')[0], tagsTable)
        };
    })

    // tag autocomplete
    $('#id_tags.typeahead').typeahead({
        minLength: 3,
        highlight: true
    }, {
        name: 'tags-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function (element) {
            return element.name
        },
        source: function (query, processSync, processAsync) {
            jsonRPC('Tag.filter', { name__icontains: query }, function (data) {
                // b/c tags are now annotated with case, run, plan IDs there are duplicate names.
                // Filter them out by only looking at Tag.id uniqueness!
                data = arrayToDict(data)
                return processAsync(Object.values(data))
            })
        }
    })
}

function populateVersion () {
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

function populateBuild () {
    const versionId = $('#id_version').val()

    if (versionId === null) {
        $('#add_id_build').addClass('disabled')
    } else {
        $('#add_id_build').removeClass('disabled')
    }

    const href = $('#add_id_build')[0].href
    $('#add_id_build')[0].href = href.slice(0, href.indexOf('&version'))
    $('#add_id_build')[0].href += `&version=${versionId}`
    updateBuildSelectFromVersion()
}

function populateCategory () {
    const productId = $('#id_product').val()

    if (productId === null) {
        $('#add_id_category').addClass('disabled')
    } else {
        $('#add_id_category').removeClass('disabled')
    }

    const href = $('#add_id_category')[0].href
    $('#add_id_category')[0].href = href.slice(0, href.indexOf('&product'))
    $('#add_id_category')[0].href += `&product=${productId}`
    $('#id_category').find('option').remove()
    updateCategorySelectFromProduct()
}

// hooks events into DataTable pagination controls
function hookIntoPagination (tableSelector, table) {
    const updateCurrentPage = function (table) {
        const info = table.page.info()
        $('.current-page').val(info.page + 1)
        $('.total-pages').html(info.pages)

        if (info.page === 0) {
            $('.pagination-pf-back').find('li').addClass('disabled')
        } else {
            $('.pagination-pf-back').find('li').removeClass('disabled')
        }

        if (info.page === info.pages - 1) {
            $('.pagination-pf-forward').find('li').addClass('disabled')
        } else {
            $('.pagination-pf-forward').find('li').removeClass('disabled')
        }
    }

    // hook into pagination controls
    $('.next-page').click(function () {
        table.page('next').draw('page')
    })

    $('.last-page').click(function () {
        table.page('last').draw('page')
    })

    $('.previous-page').click(function () {
        table.page('previous').draw('page')
    })

    $('.first-page').click(function () {
        table.page('first').draw('page')
    })

    // updates after page change
    $(tableSelector).on('page.dt', function () {
        updateCurrentPage(table)
    })

    // updates after sort
    $(tableSelector).on('order.dt', function () {
        updateCurrentPage(table)
    })

    // hide the select checkboxes if not in use
    if (window.location.href.indexOf('allow_select') === -1) {
        $(tableSelector).on('draw.dt', function () {
            $('.js-select-checkbox').hide()
        })
    }
}

const bugDetailsCache = {}

function loadBugs (selector, filter) {
    const noRecordsFoundText = $('.bugs-table').data('no-records-found-text')

    $(selector).DataTable({
        ajax: (data, callback, settings) => {
            dataTableJsonRPC('TestExecution.get_links', filter, callback)
        },
        columns: [
            {
                data: null,
                render: (data, type, full, meta) => `<a href="${data.url}" class="bug-url">${data.url}</a>`
            },
            {
                data: null,
                render: (data, type, full, meta) => `<a href="#bugs" data-toggle="popover" data-html="true"
                        data-content="undefined" data-trigger="focus" data-placement="top">
                        <span class="fa fa-info-circle"></span>
                        </a>`
            }
        ],
        dom: 't',
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: noRecordsFoundText
        },
        order: [[0, 'asc']]
    })

    $(selector).on('draw.dt', () => {
        $(selector).find('[data-toggle=popover]')
            .popovers()
            .on('show.bs.popover', (element) => {
                fetchBugDetails(
                    $(element.target).parents('tr').find('.bug-url')[0],
                    element.target)
            })
    })

    $('[data-toggle=popover]')
        .popovers()
        .on('show.bs.popover', (element) => {
            fetchBugDetails(
                $(element.target).parents('.list-view-pf-body').find('.bug-url')[0],
                element.target
            )
        })
}

function fetchBugDetails (source, popover, cache = bugDetailsCache) {
    if (source.href in cache) {
        assignPopoverData(source, popover, cache[source.href])
        return
    }

    jsonRPC('Bug.details', [source.href], data => {
        cache[source.href] = data
        assignPopoverData(source, popover, data)
    }, true)
}

function assignPopoverData (source, popover, data) {
    source.title = data.title
    $(popover).attr('data-original-title', data.title)
    $(popover).attr('data-content', data.description)
}

// https://gist.github.com/iperelivskiy/4110988#gistcomment-2697447
// used only to hash strings to get unique IDs for href targets
function funhash (s) {
    let h = 0xdeadbeef
    for (let i = 0; i < s.length; i++) {
        h = Math.imul(h ^ s.charCodeAt(i), 2654435761)
    }
    return (h ^ h >>> 16) >>> 0
}

function displayProperties (objectId, objectAttrName, viewMethod, removeMethod) {
    const container = $('#properties-accordion')
    const propertyTemplate = $('#property-fragment')[0].content
    const valueTemplate = $(propertyTemplate).find('template')[0].content
    const shownProperties = []
    let property = null

    const query = {}
    query[objectAttrName] = objectId

    jsonRPC(viewMethod, query, data => {
        data.forEach(element => {
            if (!shownProperties.includes(element.name)) {
                property = $(propertyTemplate.cloneNode(true))
                property.find('.js-property-name').html(element.name)

                const collapseId = 'collapse' + funhash(element.name)
                property.find('.js-property-name').attr('href', `#${collapseId}`)
                property.find('.js-panel-collapse').attr('id', collapseId)
                property.find('.js-remove-property').attr(`data-${objectAttrName}_id`, element[objectAttrName])
                property.find('.js-remove-property').attr('data-property-name', element.name)
                property.find('template').remove()

                container.find('.js-insert-here').append(property)
                shownProperties.push(element.name)
            }

            const value = $(valueTemplate.cloneNode(true))
            value.find('.js-property-value').text(element.value)
            value.find('.js-remove-value').attr('data-id', element.id)
            container.find('.js-panel-body').last().append(value)
        })

        $('.js-remove-property').click(function () {
            const sender = $(this)
            const query = { name: sender.data('property-name') }
            query[objectAttrName] = sender.data(`${objectAttrName}_id`)

            jsonRPC(removeMethod, query, function (data) {
                sender.parents('.panel').first().fadeOut(500)
            }
            )
            return false
        })

        $('.js-remove-value').click(function () {
            const sender = $(this)
            jsonRPC(removeMethod, { pk: sender.data('id') }, function (data) {
                sender.parent().fadeOut(500)
            })
            return false
        })
    })
}

function addPropertyValue (objectId, objectAttrName, viewMethod, addMethod, removeMethod) {
    const nameValue = $('#property-value-input').val().split('=')

    jsonRPC(
        addMethod,
        [objectId, nameValue[0].trim(), nameValue[1].trim()],
        function (data) {
            animate($('.js-insert-here'), function () {
                $('#property-value-input').val('')
                $('.js-insert-here').empty()

                displayProperties(objectId, objectAttrName, viewMethod, removeMethod)
            })
        }
    )
}

// binds everything in this card
function propertiesCard (objectId, objectAttrName, viewMethod, addMethod, removeMethod) {
    displayProperties(objectId, objectAttrName, viewMethod, removeMethod)

    $('.js-add-property-value').click(function () {
        addPropertyValue(objectId, objectAttrName, viewMethod, addMethod, removeMethod)
        return false
    })

    $('#property-value-input').keyup(function (event) {
        if (event.keyCode === 13) {
            addPropertyValue(objectId, objectAttrName, viewMethod, addMethod, removeMethod)
        }
    })
}
