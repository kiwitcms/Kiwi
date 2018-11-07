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
    $(selector).selectpicker('refresh');
}


/*
    Used to update a Version select when Product changes.
*/
function updateVersionSelect(data) {
    updateSelect(data, '#id_version', 'id', 'value')
}

/*
    Used for on-change event handlers
*/
function update_version_select_from_product() {
    var product_id = $('#id_product').val();
    if (product_id) {
        jsonRPC('Version.filter', {product: product_id}, updateVersionSelect);
    } else {
        updateVersionSelect([]);
    }
}

/*
    Used to update a Build select when Product changes.
*/
function updateBuildSelect(data) {
    updateSelect(data, '#id_build', 'build_id', 'name')
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
