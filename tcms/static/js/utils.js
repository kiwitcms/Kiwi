/*
    Used to update a select when something else changes.
*/
function updateSelect(data, selector, id_attr, value_attr) {
    var _select_tag = $(selector)[0];
    var new_options = '';

    // in some cases, e.g. TestRun search, the 1st <option> element is ---
    // which must always be there to indicate nothing selected
    if (_select_tag.options.length) {
        new_options = _select_tag.options[0].outerHTML;
    }

    data.forEach(function(element) {
        new_options += '<option value="' + element[id_attr] + '">' + element[value_attr] + '</option>';
    });

    _select_tag.innerHTML = new_options;

    try {
        $(selector).selectpicker('refresh');
    } catch(e) {
        console.warn(e);
    }
}


/*
    Used for on-change event handlers
*/
function update_version_select_from_product() {
    var updateVersionSelectCallback = function(data) {
        updateSelect(data, '#id_version', 'id', 'value')

        // trigger on-change handler, possibly updating build
        $('#id_version').change()
    };

    var product_id = $('#id_product').val();
    if (product_id) {
        jsonRPC('Version.filter', {product: product_id}, updateVersionSelectCallback);
    } else {
        updateVersionSelectCallback([]);
    }
}

/*
    Used for on-change event handlers
*/
function update_build_select_from_version(keep_first) {
    var updateCallback = function(data) {
        updateSelect(data, '#id_build', 'id', 'name')
    }

    if (keep_first === true) {
        // pass
    } else {
        $('#id_build').find('option').remove();
    }

    const version_id = $('#id_version').val();
    if (version_id) {
        jsonRPC('Build.filter', {version: version_id}, updateCallback);
    } else {
        updateCallback([]);
    }
}

/*
    Used for on-change event handlers
*/
function update_category_select_from_product() {
    var updateCallback = function(data) {
        updateSelect(data, '#id_category', 'id', 'name')
    }

    var product_id = $('#id_product').val();
    if (product_id) {
        jsonRPC('Category.filter', {product: product_id}, updateCallback);
    } else {
        updateCallback([]);
    }
}

/*
    Used for on-change event handlers
*/
function update_component_select_from_product() {
    var updateCallback = function(data) {
        data = arrayToDict(data)
        updateSelect(Object.values(data), '#id_component', 'id', 'name')
    }

    var product_id = $('#id_product').val();
    if (product_id) {
        jsonRPC('Component.filter', {product: product_id}, updateCallback);
    } else {
        updateCallback([]);
    }
}

/*
    Split the input string by comma and return
    a list of trimmed values
*/
function splitByComma(input) {
    var result = [];

    input.split(',').forEach(function(element) {
        element = element.trim();
        if (element) {
            result.push(element);
        }
    });
    return result;
}

/*
    Given a params dictionary and a selector update
    the dictionary so we can search by tags!
    Used in search.js
*/
function updateParamsToSearchTags(selector, params) {
    var tag_list = splitByComma($(selector).val());

    if (tag_list.length > 0) {
        params['tag__name__in'] = tag_list;
    };
}


/*
    Replaces HTML characters for display in DataTables

    backslash(\), quotes('), double quotes (")
    https://github.com/kiwitcms/Kiwi/issues/78

    angle brackets (<>)
    https://github.com/kiwitcms/Kiwi/issues/234
*/
function escapeHTML(unsafe) {
  return unsafe.replace(/[&<>"']/g, function(m) {
    return ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      '\'': '&#039;'
    })[m]
  });
}


function unescapeHTML(html) {
  return html.
    replace(/&amp;/g, '&').
    replace(/&lt;/g,  '<').
    replace(/&gt;/g,  '>').
    replace(/&quot;/g, '"').
    replace(/&#039;/g, '\'');
}


function treeViewBind(selector = '.tree-list-view-pf') {
    // collapse all child rows
    $(selector).find(".list-group-item-container").addClass('hidden');

    // unbind previous events b/c this function is now reentrant
    // click the list-view heading then expand a row
    $(selector).find('.list-group-item-header').off("click").click(function (event) {
      if(!$(event.target).is('button, a, input, .fa-ellipsis-v')) {
        var $this = $(this);
        $this.find('.fa-angle-right').toggleClass('fa-angle-down');
        var $itemContainer = $this.siblings('.list-group-item-container');
        if ($itemContainer.children().length) {
          $itemContainer.toggleClass('hidden');
        }
      }
    });
}

const animate = (target, handler, time = 500) => target.fadeOut(time, handler).fadeIn(time)
const currentTimeWithTimezone = timeZone => moment().tz(timeZone).format('YYYY-MM-DD HH:mm:ss')


/* render Markdown & assign it to selector */
function markdown2HTML(input, selector) {
    // first display raw input in case user is not logged in and
    // Markdown.render returns 403 forbidden
    $(selector).html(input);

    jsonRPC('Markdown.render', unescapeHTML(input), function(result) {
        $(selector).html(unescapeHTML(result));
    });
}

function renderCommentHTML(index, comment, template, bindDeleteFunc) {
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

function bindDeleteCommentButton(objId, deleteMethod, canDelete, parentNode) {
    if (canDelete) {
        parentNode.find('.js-comment-delete-btn').click(function(event) {
            const commentId = $(event.target).parents('.js-comment-container').data('comment-id')
            jsonRPC(deleteMethod, [objId, commentId], function(result) {
                $(event.target).parents('.js-comment-container').hide()
            })

            return false;
        })
    } else {
        parentNode.find('.js-comment-delete-btn').hide()
    }
}

function renderCommentsForObject(objId, getMethod, deleteMethod, canDelete, parentNode) {
    const commentTemplate = $('template#comment-template')[0];

    jsonRPC(getMethod, [objId], comments => {
        comments.forEach((comment, index) => parentNode.append(renderCommentHTML(index+1, comment, commentTemplate)))

        bindDeleteCommentButton(objId, deleteMethod, canDelete, parentNode)
    })
}

function showPopup(href) {
    if (href.indexOf('?') === -1) {
        href += '?nonav=1';
    } else {
        href += '&nonav=1';
    }

    const win = window.open(href, 'popup page', 'width=1024,height=612');
    win.focus();

    return win;
}

// used in testplans/get.html and testruns/get.html
// objId - PK of the object we're adding to
// rpcMethod - must accept [pk, case_id] - the method used to do the work
// href - URL of the search page
// errorMessage - message to display in case of RPC errors
function advancedSearchAndAddTestCases(objId, rpcMethod, href, errorMessage) {
    window.addTestCases = function(testCaseIDs, sender){
        let rpcErrors = 0

        // close the popup
        sender.close()

        if (testCaseIDs) {
            // monkey-patch the alert() function
            const oldAlert = window.alert;
            alert = window.alert = function(message) {
                rpcErrors += 1;
            }

            // add the selected test cases
            testCaseIDs.forEach(function(testCase) {
                jsonRPC(rpcMethod, [objId, testCase], function(result) {}, true)
            })

            // revert monkey-patch
            alert = window.alert = oldAlert;
        }

        if (rpcErrors) {
            alert(errorMessage);
        }

        // something was added so reload the page
        if (rpcErrors < testCaseIDs.length) {
            window.location.reload(true);
            // TODO: figure out how to reload above and add the new value to the page
        }
    };


    if (href.indexOf('?') === -1) {
        href += '?allow_select=1';
    } else {
        href += '&allow_select=1';
    }

    showPopup(href);

    return false;
}

// used in both testplans/get.html and testruns/get.html to initialize and
// handle the quicksearch widget
// objId - PK of the object we're adding to
// pageCallback - function which performs the actual RPC call of adding
//                the selected TC to objId and refreshes the page
// cache - cache of previous values fetched for typeahead
// initialQuery - an initial RPC query that is AND'ed to the internal conditions
//                for example: filter only CONFIRMED TCs.
function quickSearchAndAddTestCase(objId, pageCallback, cache, initialQuery = {}) {
    // + button
    $('#btn-add-case').click(function() {
        pageCallback(objId)

        return false
    });

    // Enter key
    $('#search-testcase').keyup(function(event) {
        if (event.keyCode === 13) {
            pageCallback(objId)

            return false
        };
    });

    // autocomplete
    $('#search-testcase.typeahead').typeahead({
        minLength: 1,
        highlight: true
        }, {
        name: 'testcases-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function(element) {
            const displayName = `TC-${element.id}: ${element.summary}`;
            cache[displayName] = element;
            return displayName;
        },
        source: function(query, processSync, processAsync) {
            // accepts "TC-1234" or "tc-1234" or "1234"
            query = query.toLowerCase().replace('tc-', '');
            if (query === '') {
                return;
            }

            var rpc_query = {pk: query};

            // or arbitrary string
            if (isNaN(query)) {
                if (query.length >=3) {
                    rpc_query = {summary__icontains: query};
                } else {
                    return;
                }
            }

            // merge initial query for more filtering if specified
            rpc_query = Object.assign({}, rpc_query, initialQuery)

            jsonRPC('TestCase.filter', rpc_query, function(data) {
                return processAsync(data);
            });
        }
    });
}

// on dropdown change update the label of the button and set new selected list item
function changeDropdownSelectedItem(dropDownSelector, buttonSelector, target, focusTarget) {
    $(`${buttonSelector}`)[0].innerHTML = target.innerText + '<span class="caret"></span>';

    //remove selected class
    $(`${dropDownSelector} li`).each(function(index, el) {
        el.className = '';
    });

    // target is a tag
    target.parentElement.className = 'selected';

    // close the parent menu
    $(target).parents('.open').toggleClass('open')

    // clear the text & the current filter
    if (focusTarget) {
        focusTarget.val('').keyup().focus();
    }

    // don't follow links
    return false;
}

function arrayToDict(arr) {
    return arr.reduce(function(map, obj) {
        map[obj.id] = obj;
        return map;
    }, {});
}


function updateTestPlanSelectFromProduct(callback = () => {}) {
    const updateCallback = (data = []) => {
        updateSelect(data, '#id_test_plan', 'id', 'name');
        callback();
    };

    const productId = $('#id_product').val();
    if (!productId) {
        updateCallback();
    } else {
        jsonRPC('TestPlan.filter', {product: productId}, updateCallback);
    }
}
