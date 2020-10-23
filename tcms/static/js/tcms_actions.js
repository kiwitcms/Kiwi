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
    'tree_reloaded': 'The tree has been reloaded.',
    'last_case_run': 'It is the last case run',
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

function getDialog(element) {
  if (!element) {
    var element = jQ('#dialog')[0];
  }

  return element;
}

function getAjaxLoading(id) {
  var e = jQ('<div>', {'class': 'ajax_loading'})[0];
  if (id) {
    e.id = id;
  }

  return e;
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
