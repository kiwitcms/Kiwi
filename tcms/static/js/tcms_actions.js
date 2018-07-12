// Create a dictionary to avoid polluting the global namespace:
var Nitrate = window.Nitrate || {}; // Ironically, this global name is not respected. So u r on ur own.
window.Nitrate = Nitrate;

Nitrate.Utils = {};
var short_string_length = 100;
var nil;

/*
    Utility function.
    Set up a function callback for after the page has loaded
 */
Nitrate.Utils.after_page_load = function(callback) {
  var that = this;
  jQ(window).bind('load', callback);
};

Nitrate.Utils.enableShiftSelectOnCheckbox = function (className){
  jQ('.' + className).shiftcheckbox();
};

Nitrate.Utils.convert = function(argument, data) {
  switch(argument) {
    case 'obj_to_list':
      if (data.length != 0 && !data.length) {
        var data = jQ.extend({}, {0: data, length: 1});
      }
      return data;
      break;
  };
};

Nitrate.Utils.formSerialize = function(f) {
  var params = {};
  jQ(f).serializeArray().forEach(function(param) {
    if (params[param.name]) {
      if (!jQ.isArray(params[param.name])) {
        params[param.name] = [params[param.name]];
      }
      params[param.name].push(param.value);
    } else {
      params[param.name] = param.value;
    }
  });
  return params;
};

jQ(window).bind('load', function(e) {
  // Initial the drop menu
  jQ('.nav_li').hover(
    function() { jQ(this).children(':eq(1)').show(); },
    function() { jQ(this).children(':eq(1)').hide(); }
  );
});

var default_messages = {
  'alert': {
    'no_case_selected': 'No cases selected! Please select at least one case.',
    'no_category_selected': 'No category selected! Please select a category firstly.',
    'ajax_failure': 'Communication with server got some unknown errors.',
    'tree_reloaded': 'The tree has been reloaded.',
    'last_case_run': 'It is the last case run',
    'invalid_bug_id': 'Please input a valid bug id!',
    'no_bugs_specified': 'Please specify bug ID',
    'no_plan_specified': 'Please specify one plan at least.'
  },
  'confirm': {
    'change_case_status': 'Are you sure you want to change the status?',
    'change_case_priority': 'Are you sure you want to change the priority?',
    'remove_case_component': 'Are you sure you want to delete these component(s)?\nYou cannot undo.',
    'remove_case_component': 'Are you sure you want to delete these component(s)?\nYou cannot undo.',
    'remove_comment': 'Are you sure to delete the comment?',
    'remove_tag': 'Are you sure you wish to delete the tag(s)'
  },
  'link': {
    'hide_filter': 'Hide filter options',
    'show_filter': 'Show filter options',
  },
  'prompt': { 'edit_tag': 'Please type your new tag' },
  'report': {
    'hide_search': 'Hide the coverage search',
    'show_search': 'Show the coverage search'
  },
  'search': {
    'hide_filter': 'Hide Case Information Option',
    'show_filter': 'Show Case Information Option',
  }
};


/*
 * http namespace and modules
 */
(function() {
  var http = Nitrate.http || {};

  http.URLConf = {
    _mapping: {
      login: '/accounts/login/',
      logout: '/accounts/logout/',

      change_user_group: '/management/account/$id/changegroup/',
      change_user_status: '/management/account/$id/changestatus/',

      modify_plan : '/plan/$id/modify/',
      plan_assign_case: '/plan/$id/assigncase/apply/',
      plans: '/plans/',

      case_change_status: '/cases/changestatus/',
      case_details: '/case/$id/',
      case_plan: '/case/$id/plan/',
      case_run_bug: '/caserun/$id/bug/',
      cases_automated: '/cases/automated/',
      cases_category: '/cases/category/',
      cases_component: '/cases/component/',
      change_case_order: '/case/$id/changecaseorder/',
      change_case_run_order: '/run/$id/changecaserunorder/',
      change_case_run_status: '/run/$id/execute/changestatus/',
      create_case: '/case/create/',
      modify_case: '/case/$id/modify/',
      search_case: '/cases/',

      manage_env_categories: '/management/environments/categories/',
      manage_env_properties: '/management/environments/properties/',
      manage_env_property_values: '/management/environments/propertyvalues/',
      runs_env_value: '/runs/env_value/'
    },

    reverse: function(options) {
      var name = options.name;
      if (name === undefined) {
        return undefined;
      }
      var arguments = options.arguments || {};
      var urlpattern = this._mapping[name];
      if (urlpattern === undefined) {
          return undefined;
      }
      var url = urlpattern;
      for (var key in arguments) {
          url = url.replace('$' + key, arguments[key].toString());
      }
      return url;
    }
  };

  Nitrate.http = http;
}());


// Exceptions for Ajax
var json_failure = function(t) {
  returnobj = jQ.parseJSON(t.responseText);
  if (returnobj.response) {
    window.alert(returnobj.response);
  } else {
    window.alert(returnobj);
  }
  return false;
};

var html_failure = function() {
  window.alert(default_messages.alert.ajax_failure);
  return false;
};

var json_success_refresh_page = function(t) {
  returnobj = jQ.parseJSON(t.responseText);

  if (returnobj.rc == 0) {
    window.location.reload();
  } else {
    window.alert(returnobj.response);
    return false;
  }
};


function setCookie(name, value, expires, path, domain, secure) { 
  var curCookie = name + "=" + escape(value) +
    ((expires) ? "; expires=" + expires.toGMTString() : "") +
    ((path) ? "; path=" + path : "") +
    ((domain) ? "; domain=" + domain : "") +
    ((secure) ? "; secure" : "");
  document.cookie = curCookie;
}

function checkCookie() {
  var exp = new Date();
  exp.setTime(exp.getTime() + 1800000);
  // first write a test cookie
  setCookie("cookies", "cookies", exp, false, false, false);
  if (document.cookie.indexOf('cookies') != -1) {
    // now delete the test cookie
    exp = new Date();
    exp.setTime(exp.getTime() - 1800000);
    setCookie("cookies", "cookies", exp, false, false, false);

    return true;
  } else {
    return false;
  }
}

function removeItem(item, tc_estimated_time) {
  var tr_estimated_time = parseInt(jQ('#estimated_time').data('time'));
  var remain_estimated_time = tr_estimated_time - tc_estimated_time;
  var second_value = remain_estimated_time % 60;
  var minute = parseInt(remain_estimated_time / 60);
  var minute_value = minute % 60;
  var hour = parseInt(minute / 60);
  var hour_value = hour % 24;
  var day_value = parseInt(hour / 24);

  var remain_estimated_time_value = day_value ? day_value + ' ' : '';
  remain_estimated_time_value += hour_value + ':';
  remain_estimated_time_value += minute_value + ':';
  remain_estimated_time_value += second_value;

  if (!remain_estimated_time_value.length) {
    remain_estimated_time_value = '0';
  }

  jQ('#estimated_time').data('time', remain_estimated_time);
  document.getElementById('id_estimated_time').value = remain_estimated_time_value;
  jQ('#' + item).remove();
}

function splitString(str, num) {
  cut_for_dot = num - 3;

  if (str.length > num) {
    return str.substring(0, cut_for_dot) + "...";
  }

  return str;
}

/* 
    Set up the <option> children of the given <select> element.
    Preserving the existing selection (if any).

    @element: a <select> element
    @values: a list of (id, name) pairs
    @allow_blank: boolean.  If true, prepend a "blank" option
*/
function set_up_choices(element, values, allow_blank) {
  var innerHTML = "";
  var selected_ids = [];

  if (!element.multiple) {
    // Process the single select box
    selected_ids.push(parseInt(element.value));
  } else {
    // Process the select box with multiple attribute
    for (var i = 0; (node = element.options[i]); i++) {
      if (node.selected) {
        selected_ids.push(node.value);
      }
    }
  }

  // Set up blank option, if there is one:
  if (allow_blank) {
    innerHTML += '<option value="">---------</option>';
  }

  // Add an <option> for each value:
  values.forEach( function(item) {
    var item_id = item[0];
    var item_name = item[1];
    var optionHTML = '<option value="' + item_id + '"';

    var display_item_name = item_name;
    var cut_for_short = false;
    if (item_name.length > short_string_length) {
      display_item_name = splitString(item_name, short_string_length);
      var cut_for_short = true;
    }

    selected_ids.forEach(function(i) {
      if (i === item_id) {
        optionHTML += ' selected="selected"';
      }
    });

    if (cut_for_short) {
      optionHTML += ' title="' + item_name + '"';
    }

    optionHTML += '>' + display_item_name + '</option>';
    innerHTML += optionHTML;
  });

  // Copy it up to the element in the DOM:
  element.innerHTML = innerHTML;
}

function getBuildsByProductId(allow_blank, product_field, build_field) {
  if (!product_field) {
    var product_field = jQ('#id_product')[0];
  }

  if (!build_field) {
    if (jQ('#id_build').length) {
      var build_field = jQ('#id_build')[0];
    } else {
      window.alert('Build field does not exist');
      return false;
    }
  }

  var product_id = jQ(product_field).val();
  no_product_is_selected = product_id === '' || product_id === null;
  if (no_product_is_selected) {
    jQ(build_field).html('<option value="">---------</option>');
    return false;
  }

  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    set_up_choices(
      build_field,
      returnobj.map(function(o) { return [o.pk, o.fields.name]; }),
      allow_blank
    );
  };

  getInfo({'info_type': 'builds', 'product_id': product_id, 'is_active': true},
          success);
}


function getVersionsByProductId(allow_blank, product_field, version_field) {
  var product_field = jQ('#id_product')[0];

  if (!version_field) {
    if (jQ('#id_product_version').length) {
      var version_field = jQ('#id_product_version')[0];
    } else {
      window.alert('Version field does not exist');
      return false;
    }
  }

  product_id = jQ(product_field).val();

  if (product_id == "" && allow_blank) {
    jQ(version_field).html('<option value="">---------</option>');
      return true;
  }

  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    set_up_choices(
      version_field,
      returnobj.map(function(o) {
        return [o.pk, o.fields.value];
      }),
      allow_blank
    );
  };

  getInfo({'info_type': 'versions', 'product_id': product_id},
          success);
}

function getComponentsByProductId(allow_blank, product_field, component_field, callback, parameters) {
  if (!parameters) {
    var parameters = {};
  }

  parameters.info_type = 'components';

  // Initial the product get from
  if (!parameters || !parameters.product_id) {
    if (!product_field) {
      var product_field = jQ('#id_product')[0];
    }
    product_id = jQ(product_field).val();
    parameters.product_id = product_id;
  }

  if (!component_field) {
    if (jQ('#id_component').length) {
      var component_field = jQ('#id_component')[0];
    } else {
      window.alert('Component field does not exist');
      return false;
    }
  }

  if (parameters.product_id === '') {
    jQ(component_field).html('<option value="">---------</option>');
    return true;
  }

  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    set_up_choices(
      component_field,
      returnobj.map(function(o) {
        return [o.pk, o.fields.name];
      }),
      allow_blank
    );

    if (typeof callback === 'function') {
      callback.call();
    }
  };

  getInfo(parameters, success);
}

function getCategorisByProductId(allow_blank, product_field, category_field) {
  if (!product_field) {
    var product_field = jQ('#id_product')[0];
  }

  product_id = jQ(product_field).val();

  if (!category_field) {
    if (jQ('#id_category').length) {
      var category_field = jQ('#id_category')[0];
    } else {
      window.alert('Category field does not exist');
      return false;
    }
  }

  if (product_id === '') {
    jQ(category_field).html('<option value="">---------</option>');
    return true;
  }

  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    set_up_choices(
      category_field,
      returnobj.map(function(o) {
        return [o.pk, o.fields.name];
      }),
      allow_blank
    );
  };

  getInfo({'info_type': 'categories', 'product_id': product_id},
          success);
}

function checkProductField(product_field) {
  if (product_field) {
    return product_field;
  }

  if (jQ('#id_product').length) {
    return jQ('#id_product')[0];
  }

  return false;
}

function bind_build_selector_to_product(allow_blank, product_field, build_field) {
  var product_field = checkProductField(product_field);

  if (product_field) {
    jQ(product_field).bind('change', function() {
      getBuildsByProductId(allow_blank, product_field, build_field);
    });

    getBuildsByProductId(allow_blank, product_field, build_field);
  }
}


function bind_version_selector_to_product(allow_blank, load, product_field, version_field) {
  var product_field = checkProductField(product_field);

  if (product_field) {
    jQ(product_field).bind('change', function() {
      getVersionsByProductId(allow_blank, product_field, version_field);
    });
    if (load) {
      getVersionsByProductId(allow_blank, product_field, version_field);
    }
  }
}

function bind_category_selector_to_product(allow_blank, load, product_field, category_field) {
  var product_field = checkProductField(product_field);

  if (product_field) {
    jQ(product_field).bind('change', function() {
      getCategorisByProductId(allow_blank, product_field, category_field);
    });
    if (load) {
      getCategorisByProductId(allow_blank);
    }
  }
}

function bind_component_selector_to_product(allow_blank, load, product_field, component_field) {
  var product_field = checkProductField(product_field);

  if (product_field) {
    jQ(product_field).bind('change', function() {
      getComponentsByProductId(allow_blank, product_field, component_field);
    });

    if (load) {
      getComponentsByProductId(allow_blank);
    }
  }
}

function myCustomURLConverter(url, node, on_save) {
  return url;
}

// Stolen from http://www.webdeveloper.com/forum/showthread.php?t=161317
function fireEvent(obj,evt) {
  var fireOnThis = obj;
  if (document.createEvent) {
    var evObj = document.createEvent('MouseEvents');
    evObj.initEvent( evt, true, false );
    fireOnThis.dispatchEvent(evObj);
  } else if(document.createEventObject) {
    fireOnThis.fireEvent('on'+evt);
  }
}

// Stolen from http://stackoverflow.com/questions/133925/javascript-post-request-like-a-form-submit
function postToURL(path, params, method) {
  method = method || "post"; // Set method to post by default, if not specified.

  // The rest of this code assumes you are not using a library.
  // It can be made less wordy if you use one.
  var form = document.createElement("form");
  form.setAttribute("method", method);
  form.setAttribute("action", path);

  for(var key in params) {
    if (typeof params[key] === 'object') {
      for (var i in params[key]) {
        if (typeof params[key][i] !== 'string') {
          continue;
        }

        var hiddenField = document.createElement("input");
        hiddenField.setAttribute("type", "hidden");
        hiddenField.setAttribute("name", key);
        hiddenField.setAttribute("value", params[key][i]);
        form.appendChild(hiddenField);
      }
    } else {
      var hiddenField = document.createElement("input");
      hiddenField.setAttribute("type", "hidden");
      hiddenField.setAttribute("name", key);
      hiddenField.setAttribute("value", params[key]);
      form.appendChild(hiddenField);
    }
  }

  document.body.appendChild(form);    // Not entirely sure if this is necessary
  form.submit();
}

function constructTagZone(container, parameters) {
  jQ(container).html('<div class="ajax_loading"></div>');

  var complete = function(t) {
    jQ('#id_tags').autocomplete({
      'source': function(request, response) {
        getInfo({'info_type': 'tags', 'name__startswith': request.term},
                function(data) {
                    var processedData = [];
                    jQ.parseJSON(data.responseText).forEach(function (element){
                        processedData.push(element.fields.name);
                    });
                    response(processedData);
                });
      },
      'minLength': 2,
      'appendTo': '#id_tags_autocomplete'
    });

    jQ('#id_tag_form').bind('submit', function(e){
      e.stopPropagation();
      e.preventDefault();

      constructTagZone(container, Nitrate.Utils.formSerialize(this));
    });
    var count = jQ('tbody#tag').attr('count');
    jQ('#tag_count').text(count);
  };

  jQ.ajax({
    'url': '/management/tags/',
    'type': 'GET',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
    },
    'complete': function () {
      complete();
    }
  });
}


function addTag(container) {
  var tag_name = jQ('#id_tags').attr('value');
  if (!tag_name.length) {
    jQ('#id_tags').focus();
  } else {
    constructTagZone(container, Nitrate.Utils.formSerialize(jQ('#id_tag_form')[0]));
  }
}

function removeTag(container, tag) {
  jQ('#id_tag_form').parent().find('input[name="a"]')[0].value = 'remove';

  var parameters = Nitrate.Utils.formSerialize(jQ('#id_tag_form')[0]);
  parameters.tags = tag;

  constructTagZone(container, parameters);
}

function removeComment(form, callback) {
  var url = form.action;
  var method = form.method;
  var parameters = Nitrate.Utils.formSerialize(form);

  jQ.ajax({
    'url': url,
    'type': method,
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      updateCommentsCount(parameters['object_pk'], false);
      callback(jqXHR);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}


function submitComment(container, parameters, callback) {
  var complete = function(t) {
    updateCommentsCount(parameters['case_id'], true);
    if (callback) {
      callback();
    }
  };

  jQ(container).html('<div class="ajax_loading"></div>');

  var url = '/comments/post/';
  jQ.ajax({
    'url': url,
    'type': 'POST',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
    },
    'complete': function () {
      complete();
    }
  });
}

function updateCommentsCount(caseId, increase) {
  var commentDiv = jQ("#"+caseId+"_case_comment_count");
  var countText = jQ("#"+caseId+"_comments_count");
  if (increase) {
    if (commentDiv.children().length === 1) {
      commentDiv.prepend("<img src=\"/static/images/comment.png\" style=\"vertical-align: middle;\">");
    }
    countText.text(" " + (parseInt(countText.text()) + 1));
  } else {
    var count = parseInt(countText.text(), 10);
    if (count === 1) {
      commentDiv.html("<span id=\""+caseId+"_comments_count\"> 0</span>");
    } else {
      countText.text(" " + (parseInt(commentDiv.text()) - 1));
    }
  }
}

function previewPlan(parameters, action, callback) {
  var dialog = getDialog();

  clearDialog();
  jQ(dialog).show();

  parameters.t = 'html';
  parameters.f = 'preview';

  var url = '/plans/';
  var success = function(t) {
    var form = constructForm(t.responseText, action, callback);
    jQ(dialog).html(form);
  };

  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      success(jqXHR);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      html_failure();
    }
  });
}

function getInfo(parameters, callback) {
  jQ.ajax({
    'url': '/management/getinfo/',
    'type': 'GET',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
        callback(jqXHR);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
        window.alert("Get info " + parameters.info_type + " failed");
        return false;
    }
  });
}


function getDialog(element) {
  if (!element) {
    var element = jQ('#dialog')[0];
  }

  return element;
}

var showDialog = function(element) {
  var dialog = getDialog(element);
  return jQ(dialog).show()[0];
};

var clearDialog = function(element) {
  var dialog = getDialog(element);

  jQ(dialog).html(getAjaxLoading());
  return jQ(dialog).hide()[0];
};

function getAjaxLoading(id) {
  var e = jQ('<div>', {'class': 'ajax_loading'})[0];
  if (id) {
    e.id = id;
  }

  return e;
}

function clickedSelectAll(checkbox, form, name) {
  var checkboxes = jQ(form).parent().find('input[name='+ name + ']');
  for (i = 0; i < checkboxes.length; i++) {
	checkboxes[i].checked = checkbox.checked? true:false;
  }
}

function bindSelectAllCheckbox(element, form, name) {
  jQ(element).bind('click', function(e) {
    clickedSelectAll(this, form, name);
  });
}

function constructForm(content, action, form_observe, info, s, c) {
  var f = jQ('<form>', {'action': action});
  var i = jQ('<div>', {'class': 'alert'});
  if (info) {
    i.html(info);
  }

  if (!s) {
    var s = jQ('<input>', {'type': 'submit', 'value': 'Submit'});
  }

  if (!c) {
    var c = jQ('<input>', {'type': 'button', 'value': 'Cancel'});
    c.bind('click', function(e) {
      clearDialog();
    });
  }

  if (form_observe) {
    f.bind('submit', form_observe);
  }

  f.html(content);
  f.append(i);
  f.append(s);
  f.append(c);

  return f[0];
}

var reloadWindow = function(t) {
  if (t) {
    var returnobj = jQ.parseJSON(t.responseText);
    if (returnobj.rc !== 0) {
      window.alert(returnobj.response);
      return false;
    }
  }

  window.location.reload(true);
};

// Enhanced from showAddAnotherPopup in RelatedObjectLookups.js for Admin
// todo: this duplicates existing functionality in admin/grappelli in the
// above mentioned JS files. Needs to be refactored.
function popupAddAnotherWindow(triggeringLink, parameters) {
  var name = triggeringLink.id.replace(/^add_/, '');
  name = id_to_windowname(name);
  href = triggeringLink.href;
  if (href.indexOf('?') === -1) {
    href += '?_popup=1';
  } else {
    href += '&_popup=1';
  }

  // IMPOROMENT: Add parameters.
  // FIXME: Add multiple parameters here
  if (parameters) {
    href += '&' + parameters + '=' + jQ('#id_' + parameters).val();
  }

  var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=no');
  win.focus();
  return false;
}

function exportCase(url, form, table) {
  var selection = serializeCaseFromInputList2(table);
  var emptySelection = !selection.selectAll & selection.selectedCasesIds.length === 0;
  if (emptySelection) {
    window.alert(default_messages.alert.no_case_selected);
    return false;
  }

  var params = serialzeCaseForm(form, table, true);
  if (selection.selectAll) {
    params.selectAll = selection.selectAll;
  }
  // replace with selected cases' IDs
  params.case = selection.selectedCasesIds;
  postToURL(url, params);
}

var printableCases = exportCase;

function validateIssueID(bugRegExp, bugId) {
  // if bugRegExp is empty string then all input is valid!
  if (!bugRegExp) {
    return true;
  }

  try {
    var bug_re = new RegExp(bugRegExp);
  // catch syntax errors in regular expressions
  } catch(err) {
    window.alert(err.name + ': ' + err.message);
    return false;
  }
  var result = bug_re.test(bugId);

  if (!result) {
    window.alert(default_messages.alert.invalid_bug_id);
  }
  return result;
}
