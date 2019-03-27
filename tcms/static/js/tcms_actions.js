if (!jQ) {
    var jQ = $;
}

// Create a dictionary to avoid polluting the global namespace:
var Nitrate = window.Nitrate || {}; // Ironically, this global name is not respected. So u r on ur own.
window.Nitrate = Nitrate;

Nitrate.Utils = {};
var short_string_length = 100;

/*
    Utility function.
    Set up a function callback for after the page has loaded
 */
Nitrate.Utils.after_page_load = function(callback) {
  var that = this;
  jQ(window).bind('load', callback);
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

var default_messages = {
  'alert': {
    'no_case_selected': 'No cases selected! Please select at least one case.',
    'no_category_selected': 'No category selected! Please select a category firstly.',
    'ajax_failure': 'Communication with server got some unknown errors.',
    'tree_reloaded': 'The tree has been reloaded.',
    'last_case_run': 'It is the last case run',
    'invalid_bug_id': 'Please input a valid bug id!',
    'no_bugs_specified': 'Please specify bug ID',
  },
  'confirm': {
    'change_case_status': 'Are you sure you want to change the status?',
    'change_case_priority': 'Are you sure you want to change the priority?',
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

      case_details: '/case/$id/',
      search_case: '/cases/',
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


function splitString(str, num) {
  cut_for_dot = num - 3;

  if (str.length > num) {
    return str.substring(0, cut_for_dot) + "...";
  }

  return str;
}

// todo: remove this
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

// todo: remove this
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

/*
    Used to configure autocomplete for 'Add Tag' widgets
*/
function setAddTagAutocomplete() {
    jQ('#id_tags').autocomplete({
        'source': function(request, response) {
            jsonRPC('Tag.filter', {'name__startswith': request.term}, function(data) {
                var processedData = [];
                data.forEach(function(element) {
                    processedData.push(element.name);
                });
                response(processedData);
            });
        },
        'minLength': 2,
        'appendTo': '#id_tags_autocomplete'
    });
}


function constructTagZone(container, parameters) {
  $(container).html('<div class="ajax_loading"></div>');

  var complete = function(t) {
    setAddTagAutocomplete();

    $('#id_tag_form').bind('submit', function(e){
      e.stopPropagation();
      e.preventDefault();

      addTag(container);
    });
    var count = $('tbody#tag').attr('count');
    $('#tag_count').text(count);
  };

  $.ajax({
    'url': '/management/tags/',
    'type': 'GET',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      $(container).html(data);
    },
    'complete': function () {
      complete();
    }
  });
}


// add tag to TestPlan or TestCase
// called from the 'Tabs' tab in the get view
function addTag(container) {
    var tags = $('#id_tags')[0];
    var tag_name = tags.value;
    var params = $(tags).data('params');
    var method = params[0] + '.add_tag';
    var search_params = {};
    search_params[params[0].replace('Test', '').toLowerCase()] = params[1];

    if (tag_name.length > 0) {
        jsonRPC(method, [params[1], tag_name], function(data) {
            constructTagZone(container, search_params);
        });
    }
}


// remove tag from TestPlan or TestCase
// called from the 'Tabs' tab in the get view
function removeTag(container, params) {
    var method = params[0] + '.remove_tag';
    var search_params = {};
    search_params[params[0].replace('Test', '').toLowerCase()] = params[1];

    jsonRPC(method, [params[1], params[2]], function(data) {
        constructTagZone(container, search_params);
    });
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

function getDialog(element) {
  if (!element) {
    var element = jQ('#dialog')[0];
  }

  return element;
}

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

function printableCases(url, form, table) {
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
