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
function update_build_select_from_product(keep_first) {
    var updateCallback = function(data) {
        updateSelect(data, '#id_build', 'id', 'name')
    }

    if (keep_first === true) {
        // pass
    } else {
        $('#id_build').find('option').remove();
    }

    var product_id = $('#id_product').val();
    if (product_id) {
        jsonRPC('Build.filter', {product: product_id}, updateCallback);
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
        updateSelect(data, '#id_component', 'id', 'name')
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


/* render Markdown & assign it to selector */
function markdown2HTML(input, selector) {
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

function filterTestCasesByProperty(planId, testCases, filterBy, filterValue) {
    // no input => show all rows
    if (filterValue.trim().length === 0) {
        $('.js-testcase-row').show();
        return;
    }

    $('.js-testcase-row').hide();
    if (filterBy === 'component' || filterBy === 'tag') {
        let query = {plan: planId}
        query[`${filterBy}__name__icontains`] = filterValue

        jsonRPC('TestCase.filter', query, function(filtered) {
            // hide again if a previous async request showed something else
            $('.js-testcase-row').hide();
            filtered.forEach(tc => $(`[data-testcase-pk=${tc.id}]`).show());
        })
    } else {
        testCases.filter(function(tc){
            return (tc[filterBy] && tc[filterBy].toString().toLowerCase().indexOf(filterValue) > -1)
        }).forEach(tc => $(`[data-testcase-pk=${tc.id}]`).show());
    }
}
