Nitrate.TestRuns = {};
Nitrate.TestRuns.List = {};
Nitrate.TestRuns.Details = {};
Nitrate.TestRuns.New = {};
Nitrate.TestRuns.Edit = {};
Nitrate.TestRuns.Execute = {}
Nitrate.TestRuns.Clone = {};
Nitrate.TestRuns.ChooseRuns = {};
Nitrate.TestRuns.AssignCase = {}

Nitrate.TestRuns.List.on_load = function() {
  bind_version_selector_to_product(true, jQ('#id_product')[0]);
  bind_build_selector_to_product(true, jQ('#id_product')[0]);

  if (jQ('#id_people_type').length) {
    jQ('#id_search_people').attr('name', jQ('#id_people_type').val());
    jQ('#id_people_type').bind('change', function() {
      jQ('#id_search_people').attr('name', jQ('#id_people_type').val());
    });
  }

  if (jQ('#run_column_add').length) {
    jQ('#run_column_add').bind('change', function(t) {
      switch(this.value) {
        case 'col_plan':
          jQ('#col_plan_head').show();
          jQ('.col_plan_content').show();
          jQ('#col_plan_option').hide();
          break;
      };
    });
  }

  if (!jQ('#testruns_table').hasClass('js-advance-search-runs')) {
    var oTable = jQ('#testruns_table').dataTable({
      "iDisplayLength": 20,
      "sPaginationType": "full_numbers",
      "bFilter": false,
      "bLengthChange": false,
      "aaSorting": [[ 1, "desc" ]],
      "bProcessing": true,
      "bServerSide": true,
      "sAjaxSource": "/runs/ajax/" + this.window.location.search,
      "aoColumns": [
        {"sType": "numeric"},
        {"sType": "html"},
        {"sType": "html"},
        {"sType": "html"},
        {"bVisible": false},
        null,
        null,
        null,
        {"sType": "numeric", "bSortable": false},
        null,
        {"bSortable": false }
      ],
      "oLanguage": { "sEmptyTable": "No run was found." }
    });
  }
};

Nitrate.TestRuns.Details.on_load = function() {
  // Observe the interface buttons
  jQ('#id_check_all_button').bind('click', function(e) {
    toggleAllCheckBoxes(this, 'id_table_cases', 'case_run');
  });

  Nitrate.Utils.enableShiftSelectOnCheckbox('caserun_selector');

  if (jQ('#id_check_box_highlight').attr('checked')) {
    jQ('.mine').addClass('highlight');
  }

  jQ('#id_check_box_highlight').bind('click', function(e) {
    e = jQ('.mine');
    this.checked && e.addClass('highlight') || e.removeClass('highlight');
  });

  jQ('#id_blind_all_link').bind('click', function(e) {
    if (!jQ('td[id^="id_loading_"]').length) {
      jQ(this).removeClass('locked');
    }
    if (jQ(this).is('.locked')) {
      //To disable the 'expand all' until all case runs are expanded.
      return false;
    } else {
      jQ(this).addClass('locked');
      var element = jQ(this).children();
      if (element.is('.collapse-all')) {
        this.title = "Collapse all cases";
        blinddownAllCases(element[0]);
      } else {
        this.title = "Expand all cases";
        blindupAllCases(element[0]);
      }
    }
  });

  // Observe the case run toggle and the comment form
  var toggle_case_run = function(e) {
    var c = jQ(this).parent(); // Container
    var c_container = c.next(); // Content Containers
    var case_id = c.find('input[name="case"]')[0].value;
    var case_run_id = c.find('input[name="case_run"]')[0].value;
    var case_text_version = c.find('input[name="case_text_version"]')[0].value;
    var type = 'case_run';
    var callback = function(t) {
      // Observe the update case run stauts/comment form
      c_container.parent().find('.update_form')
        .unbind('submit').bind('submit', updateCaseRunStatus);

      // Observe the delete comment form
      var refresh_case = function(t) {
        constructCaseRunZone(c_container[0], c[0], case_id);
      };

      var rc_callback = function(e) {
        e.stopPropagation();
        e.preventDefault();
        if (!window.confirm(default_messages.confirm.remove_comment)) {
          return false;
        }
        removeComment(this, refresh_case);
      };
      c_container.parent().find('.form_comment')
        .unbind('submit').bind('submit', rc_callback);
      c_container.find('.js-status-button').bind('click', function() {
        this.form.value.value = jQ(this).data('formvalue');
      });
      c_container.find('.js-show-comments').bind('click', function() {
        toggleDiv(this, jQ(this).data('param'));
      });
      c_container.find('.js-show-changelog').bind('click', function() {
        toggleDiv(this, jQ(this).data('param'));
      });
      c_container.find('.js-file-caserun-bug').bind('click', function(){
        var params = jQ(this).data('params');
        fileCaseRunBug(params[0], c[0], c_container[0], params[1], params[2]);
      });
      c_container.find('.js-add-caserun-bug').bind('click', function(){
        var params = jQ(this).data('params');
        addCaseRunBug(params[0], c[0], c_container[0], params[1], params[2]);
      });
      c_container.find('.js-remove-caserun-bug').bind('click', function(){
        var params = jQ(this).data('params');
        removeCaseRunBug(params[0], c[0], c_container[0], params[1], params[2], params[3]);
      });
      c_container.find('.js-add-testlog').bind('click', function(){
        var params = jQ(this).data('params');
        addLinkToCaseRun(this, params[0], params[1]);
      });
      c_container.find('.js-remove-testlog').bind('click', function(){
        removeLink(this, window.parseInt(jQ(this).data('param')));
      });
    };

    toggleTestCaseRunPane({
      'callback': callback,
      'caseId': case_id,
      'caserunId': case_run_id,
      'caseTextVersion': case_text_version,
      'caserunRowContainer': c,
      'expandPaneContainer': c_container
    });
  };
  jQ('.expandable').bind('click', toggle_case_run);

  // Auto show the case run contents.
  if (window.location.hash != '') {
    fireEvent(jQ('a[href=\"' + window.location.hash + '\"]')[0], 'click');
  };

  // Filter Case-Run
  if (jQ('#filter_case_run').length) {
    jQ('#filter_case_run').bind('click',function(e){
      if (jQ('#id_filter').is(':hidden')){
        jQ('#id_filter').show();
        jQ(this).html(default_messages.link.hide_filter);
      } else {
        jQ('#id_filter').hide();
        jQ(this).html(default_messages.link.show_filter);
      }
    });
  }
  //bind click to status btn
  jQ('.btn_status').live('click', function() {
    var from = jQ(this).siblings('.btn_status:disabled')[0].title;
    var to = this.title;
    if (jQ('span#' + to + ' a').text() === '0') {
      var htmlstr = "[<a href='javascript:void(0)' onclick=\"showCaseRunsWithSelectedStatus(jQ('#id_filter')[0], '"
        + jQ(this).attr('crs_id')+"')\">0</a>]";
      jQ('span#' + to).html(htmlstr);
    }
    if (jQ('span#' + from + ' a').text() === '1') {
      jQ('span#' + from).html("[<a>1</a>]");
    }
    jQ('span#' + to + ' a').text(window.parseInt(jQ('span#' + to + ' a').text()) + 1);
    jQ('span#' + from + ' a').text(window.parseInt(jQ('span#' + from + ' a').text()) - 1);

    var caseRunCount = window.parseInt(jQ('span#TOTAL').next().text()) || 0;
    var passedCaseRunCount = window.parseInt(jQ('span#PASSED a').text()) || 0;
    var errorCaseRunCount = window.parseInt(jQ('span#ERROR a').text()) || 0;
    var failedCaseRunCount = window.parseInt(jQ('span#FAILED a').text()) || 0;
    var waivedCaseRunCount = window.parseInt(jQ('span#WAIVED a').text()) || 0;
    var completePercent = 100 * ((passedCaseRunCount + errorCaseRunCount + failedCaseRunCount
      + waivedCaseRunCount) / caseRunCount).toFixed(2);
    var failedPercent = 100 * ((errorCaseRunCount + failedCaseRunCount) / (passedCaseRunCount
      + errorCaseRunCount + failedCaseRunCount + waivedCaseRunCount)).toFixed(2);

    jQ('span#complete_percent').text(completePercent);
    jQ('div.progress-inner').attr('style', 'width:' + completePercent + '%');
    jQ('div.progress-failed').attr('style', 'width:' + failedPercent + '%');
  });

  jQ('#btn_edit').bind('click', function() {
    var params = jQ(this).data('params');
    window.location.href = params[0] + '?from_plan=' + params[1];
  });
  jQ('#btn_clone').bind('click', function() {
    postToURL(jQ(this).data('param'), serializeCaseRunFromInputList('id_table_cases','case_run'));
  });
  jQ('#btn_delete').bind('click', function() {
    window.location.href = jQ(this).data('param');
  });
  jQ('.js-remove-tag').bind('click', function() {
    var params = jQ(this).data('params');
    removeRuntag(jQ('.js-tag-ul')[0], params[0], params[1]);
  });
  jQ('.js-add-tag').bind('click', function() {
    addRunTag(jQ('.js-tag-ul')[0], jQ(this).data('param'));
  });
  jQ('.js-set-running').bind('click', function() {
    window.location.href = jQ(this).data('param') + '?finished=0';
  });
  jQ('.js-set-finished').bind('click', function() {
    window.location.href = jQ(this).data('param') + '?finished=1';
  });
  jQ('.js-del-case').bind('click', function() {
    delCaseRun(jQ(this).data('param'));
  });
  jQ('.js-update-case').bind('click', function() {
    postToURL(jQ(this).data('param'), serializeCaseRunFromInputList('id_table_cases', 'case_run'));
  });
  jQ('.js-change-assignee').bind('click', function() {
    changeCaseRunAssignee();
  });
  jQ('.js-add-bugs').bind('click', function() {
    updateBugs('add');
  });
  jQ('.js-remove-bugs').bind('click', function() {
    updateBugs('remove');
  });
  jQ('.js-show-commentdialog').bind('click', function() {
    showCommentForm();
  });
  jQ('.js-add-cc').bind('click', function() {
    addRunCC(jQ(this).data('param'), jQ('.js-cc-ul')[0]);
  });
  jQ('.js-remove-cc').bind('click', function() {
    var params = jQ(this).data('params');
    removeRunCC(params[0], params[1], jQ('.js-cc-ul')[0]);
  });
  jQ('.js-add-property').bind('click', function() {
    var params = jQ(this).data('params');
    addProperty(params[0], params[1]);
  });
  jQ('.js-edit-property').bind('click', function() {
    var params = jQ(this).data('params');
    editValue(jQ(this).parents('form.js-run-env')[0], params[0], params[1], params[2]);
  });
  jQ('.js-remove-property').bind('click', function() {
    removeProperty(jQ(this).data('param'), this);
  });
  jQ('.js-env-submit').bind('click', function() {
    var params = jQ(this).data('params');
    submitValue(params[0],params[1],params[2], jQ(this).prev()[0], params[3]);
  });
  jQ('.js-caserun-total').bind('click', function() {
    showCaseRunsWithSelectedStatus(jQ('#id_filter')[0], '');
  });
  jQ('.js-status-subtotal').bind('click', function() {
    showCaseRunsWithSelectedStatus(jQ('#id_filter')[0], jQ(this).data('param'));
  });
};

Nitrate.TestRuns.New.on_load = function() {
  if (jQ('#testcases').length) {
    jQ('#testcases').dataTable({ "bPaginate": false, "bFilter": false, "bProcessing": true });
  }

  jQ('#add_id_product_version, #add_id_build').bind('click', function() {
    return popupAddAnotherWindow(this, 'product');
  });
  jQ('.js-cancel-button').bind('click', function() {
    window.history.go(-1);
  });
  jQ('.js-case-summary').bind('click', function() {
    toggleTestCaseContents(jQ(this).data('param'));
  });
  jQ('.js-remove-case').bind('click', function() {
    var params = jQ(this).data('params');
    removeItem(params[0], params[1]);
  });
};

Nitrate.TestRuns.Edit.on_load = function() {
  bind_version_selector_to_product(false);
  bind_build_selector_to_product(false);
  if (jQ('#id_auto_update_run_status').attr('checked')) {
    jQ('#id_finished').attr({'checked': false, 'disabled': true});
  }
  jQ('#id_auto_update_run_status').bind('click', function(){
    if (jQ('#id_auto_update_run_status').attr('checked')) {
      jQ('#id_finished').attr({'checked': false, 'disabled': true});
    } else {
      if (jQ('#id_finished').attr('disabled')) {
        jQ('#id_finished').attr('disabled', false);
      }
    }
  });
  jQ('#add_id_product_version, #add_id_build').bind('click', function() {
    return popupAddAnotherWindow(this, 'product');
  });
};

Nitrate.TestRuns.Clone.on_load = function() {
  bind_version_selector_to_product(false);
  bind_build_selector_to_product(false);
  jQ("input[type=checkbox][name^=select_property_id_]").each(function() {
    $this = jQ(this);
    $this.bind('click', function(){
      var parent = jQ(this).parent();
      if (this.checked) {
        jQ('select', parent).attr("disabled", false);
        jQ('input[type=hidden]', parent).attr("disabled", false);
      } else {
        jQ('select', parent).attr("disabled", true);
        jQ('input[type=hidden]', parent).attr("disabled", true);
      }
    });
  });

  jQ('#add_id_product_version, #add_id_build').bind('click', function() {
    return popupAddAnotherWindow(this, 'product');
  });
  jQ('.js-cancel-button').bind('click', function() {
    window.history.go(-1);
  });
  jQ('.js-remove-button').bind('click', function() {
    jQ(this).parents('.js-one-case').remove();
  });
};

Nitrate.TestRuns.ChooseRuns.on_load = function() {
  if (jQ('#id_check_all_button').length) {
    jQ('#id_check_all_button').bind('click', function(m) {
      toggleAllCheckBoxes(this, 'id_table_runs', 'run');
    });
  }
  jQ('.js-update-button').bind('click', function() {
    insertCasesIntoTestRun();
  });
  jQ('.js-help-info').bind('click', function() {
    jQ('#help_assign').show();
  });
  jQ('.js-close-help').bind('click', function() {
    jQ('#help_assign').hide();
  });
  jQ('.js-toggle-button').bind('click', function() {
    var c = jQ(this).parents('.js-one-case');
    var c_container = c.next();
    var case_id = c.find('input[name="case"]').val();
    toggleTestCasePane({ 'case_id': case_id, 'casePaneContainer': c_container }, function() {
      c_container.children().attr('colspan', 9);
    });
    toggleExpandArrow({ 'caseRowContainer': c, 'expandPaneContainer': c_container });
  });
};

Nitrate.TestRuns.AssignCase.on_load = function() {
  if (jQ('#id_check_all_button').length) {
    jQ('#id_check_all_button').bind('click', function(m) {
      toggleAllCheckBoxes(this, 'id_table_cases', 'case');
    });
  }

  jQ('input[name="case"]').bind('click', function(t) {
    if (this.checked) {
      jQ(this).closest('tr').addClass('selection_row');
      jQ(this).parent().siblings().eq(7).html('<div class="apply_icon"></div>');
    } else {
      jQ(this).closest('tr').removeClass('selection_row');
      jQ(this).parent().siblings().eq(7).html('');
    }
  });

  jQ('.js-how-assign-case').bind('click', function() {
    jQ('#help_assign').show();
  });
  jQ('.js-close-how-assign').bind('click', function() {
    jQ('#help_assign').hide();
  });
  jQ('.js-toggle-button, .js-case-summary').bind('click', function() {
    toggleTestCaseContents(jQ(this).data('param'));
  });
};


function updateRunStatus(object_pk, value, callback) {
  jQ.ajax({
    'url': '/run/case-run-update-status/',
    'type': 'POST',
    'data': {'object_pk': object_pk, 'status_id': value },
    'success': function (data, textStatus, jqXHR) {
      callback();
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

var updateCaseRunStatus = function(e) {
  e.stopPropagation();
  e.preventDefault();
  var container = jQ(this).parents().eq(3);
  var parent = container.parent();
  var title = parent.prev();
  var link = title.find('.expandable')[0];
  var parameters = Nitrate.Utils.formSerialize(this);
  var object_pk = parameters['object_pk'];
  var value = parameters['value'];

  // Callback when
  var callback = function(t) {
    // Update the contents
    if (parameters['value'] != '') {
      // Update the case run status icon
      var crs = Nitrate.TestRuns.CaseRunStatus;
      title.find('.icon_status').each(function(index) {
        for (i in crs) {
          if (typeof crs[i] === 'string' && jQ(this).is('.btn_' + crs[i])) {
            jQ(this).removeClass('btn_' + crs[i]);
          }
        }
        jQ(this).addClass('btn_' + Nitrate.TestRuns.CaseRunStatus[value - 1]);
      });

      // Update related people
      var usr = Nitrate.User;
      title.find('.link_tested_by').each(function(i) {
        jQ(this).html(usr.username);
      });
    }

    // Mark the case run to mine
    if (!title.is('.mine')) {
      title.addClass('mine');
    }

    // Blind down next case
    fireEvent(link, 'click');
    if (jQ('#id_check_box_auto_blinddown').attr('checked') && parameters['value'] != '') {
      var next_title = parent.next();
      if (!next_title.length) {
        return false;
      }
      if (next_title.next().is(':hidden')) {
        fireEvent(next_title.find('.expandable')[0], 'click');
      }
    } else {
      fireEvent(link, 'click');
    }
  };

  // Add comment
  if (parameters['comment'] != '') {
    // Reset the content to loading
    var ajax_loading = getAjaxLoading();
    ajax_loading.id = 'id_loading_' + parameters['case_id'];
    container.html(ajax_loading);
    var c = jQ('<div>');
    if (parameters['value'] != '') {
      submitComment(c[0], parameters);
    } else {
      submitComment(c[0], parameters, callback);
    }
  }

  // Update the object when changing the status
  if (parameters['value'] != '') {
    // Reset the content to loading
    var ajax_loading = getAjaxLoading();
    ajax_loading.id = 'id_loading_' + parameters['case_id'];
    container.html(ajax_loading);
    updateRunStatus([object_pk], value, callback);
  }
};


function constructCaseRunZone(container, title_container, case_id) {
  var link = jQ(title_container).find('.expandable')[0];
  if (container) {
    var td = jQ('<td>', {'id': 'id_loading_' + case_id, 'colspan': 12 });
    td.html(getAjaxLoading());
    jQ(container).html(td);
  }

  if (title_container) {
    fireEvent(link, 'click');
    fireEvent(link, 'click');
  }
}


//////////////////////////////////////////////////////////////////////////////////////////////
////////   AddIssueDialog Definition //////////////


/*
 * Dialog to allow user to add sort of issue keys to case run(s).
 *
 * Here, issue key is a general to whatever the issue tracker system is.
 *
 * options:
 * @param extraFormHiddenData: used for providing extra data for specific AJAX request.
 * @param onSubmit: callback function when user click Add button
 * @param action: string - Add or Remove. Default is Add
 */
/*
 * FIXME: which namespace is proper to hold this dialog class?
 */
function AddIssueDialog(options) {
  this.onSubmit = options.onSubmit;
  if (this.onSubmit !== undefined && typeof this.onSubmit !== "function") {
    throw new Error("onSubmit should be a function object.");
  }
  this.extraFormHiddenData = options.extraFormHiddenData;
  if (this.extraFormHiddenData !== undefined && typeof this.extraFormHiddenData !== "object") {
    throw new Error("extraFormHiddenData sould be an object if present.");
  }

  this.action = options.action;
  if (this.action === undefined) {
    this.action = "Add";
  }

  this.a = options.a;
  if (this.a === undefined) {
    this.a = this.action.toLowerCase();
  }

  if (options.hasOwnProperty("show_bug_id_field")) {
    this.show_bug_id_field = options.show_bug_id_field;
  } else {
    this.show_bug_id_field = false;
  }
}


AddIssueDialog.prototype.show = function () {
  var dialog = jQ("#dialog")[0];
  if (dialog == null) {
    throw new Error("No HTML element with ID dialog. This should not happen in the runtime.");
  }

  var hiddenPart = [];
  if (this.extraFormHiddenData !== undefined) {
    for (var name_attr in this.extraFormHiddenData) {
      hiddenPart.push({'name': name_attr, 'value': this.extraFormHiddenData[name_attr]});
    }
  }

  var template = Handlebars.compile(jQ("#add_issue_form_template").html());
  var context = {
    'hiddenFields': hiddenPart,
    'action_button_text': this.action,
    'show_bug_id_field': this.show_bug_id_field || this.action === 'Add',
    'show_add_to_bugzilla_checkbox': this.action === 'Add',
    'a': this.a,
  };

  jQ('#dialog').html(template(context))
    .find('.js-cancel-button').bind('click', function() {
      jQ('#dialog').hide();
    })
    .end().show();

  this.form = jQ("#add_issue_form")[0];

  // Used for following event callbacks to ref this dialog's instance
  var that = this;

  // Set custom callback functions
  if (this.onSubmit !== undefined) {
    jQ(this.form).bind('submit', function (form_event) {
      that.onSubmit(form_event, that);
    });
  }
};

AddIssueDialog.prototype.get_data = function () {
  var form_data = Nitrate.Utils.formSerialize(this.form);
  form_data.bug_validation_regexp = jQ('#bug_system_id option:selected').data('validation-regexp');
  return form_data;
};

//// end of AddIssueDialog definition /////////
/////////////////////////////////////////////////////////////////////////////////////////////

function getIssueTrackerNewURL() {
}

function fileCaseRunBug(run_id, title_container, container, case_id, case_run_id, callback) {
  var dialog = new AddIssueDialog({
    'action': 'Report',
    'a': 'file',
    'extraFormHiddenData': { 'case_run': case_run_id, 'case': case_id },
    'onSubmit': function (e, dialog) {
      e.stopPropagation();
      e.preventDefault();

      form_data = dialog.get_data();

      var success_callback = function(t) {
        jQ('#dialog').hide();
        var returnobj = t;

        if (returnobj.rc === 0) {
          if (callback) {
            return callback();
          }

          window.open(returnobj.response, '_blank');
          return true;
        } else {
          window.alert(returnobj.response);
          return false;
        }
      };

      var url = Nitrate.http.URLConf.reverse({ 'name': 'case_run_bug', 'arguments': {'id': case_run_id} });
      jQ.ajax({ url: url, dataType: 'json', data: form_data, success: success_callback });
    }
  });

  dialog.show();
}

function addCaseRunBug(run_id, title_container, container, case_id, case_run_id, callback) {
  var dialog = new AddIssueDialog({
    'extraFormHiddenData': { 'case_run': case_run_id, 'case': case_id },
    'onSubmit': function (e, dialog) {
      e.stopPropagation();
      e.preventDefault();

      form_data = dialog.get_data();

      form_data.bug_id = form_data.bug_id.trim();
      if (!form_data.bug_id.length) {
        return;
      }

      if (!validateIssueID(form_data.bug_validation_regexp, form_data.bug_id)) {
        return false;
      }

      var success_callback = function(t) {
        jQ('#dialog').hide();
        var returnobj = t;

        if (returnobj.rc === 0) {
          if (callback) {
            return callback();
          }

          // Update bugs count associated with just updated case run
          var jqCaserunBugCount = jQ('span#' + case_run_id + '_case_bug_count');
          if (jqCaserunBugCount.text() == '0') {
            jqCaserunBugCount.addClass('have_bug');
          }
          jqCaserunBugCount.text(returnobj.caserun_bugs_count);

          // Update the total bugs count of this run
          var html = null;
          if (jQ('span#total_run_bug_count a').text() === 'No Bugs') {
            html = "<a title='Show All Bugs' href='/run/" + run_id + "/report/#buglist'>Bugs [" + returnobj.run_bug_count + "]</a>";
            jQ('span#total_run_bug_count').html(html);
          } else {
            html = "Bugs [" + returnobj.run_bug_count + "]";
            jQ('span#total_run_bug_count a').html(html);
          }

          return constructCaseRunZone(container, title_container, case_id);
        } else {
          window.alert(returnobj.response);
          return false;
        }
      };

      var url = Nitrate.http.URLConf.reverse({ 'name': 'case_run_bug', 'arguments': {'id': case_run_id} });

      jQ.ajax({ url: url, dataType: 'json', data: form_data, success: success_callback });
    }
  });

  dialog.show();
}


function removeCaseRunBug(run_id, title_container, container, bug_id, case_id, case_run_id, callback) {
  if (!bug_id) {
    return false;
  }

  if (!window.confirm('Are you sure to remove the bug?')) {
    return false;
  }

  var url = '/caserun/' + case_run_id + '/bug/';
  var parameters = { 'a': 'remove', 'case_run': case_run_id, 'bug_id': bug_id };
  var success = function(t) {
    var returnobj = jQ.parseJSON(t.responseText);

    if (!returnobj.rc) {
      if (callback) {
        return callback();
      }
      //update bug count
      jQ('span#' + case_run_id + '_case_bug_count')
        .text(window.parseInt(jQ('span#' + case_run_id + '_case_bug_count').text()) - 1);
      if (jQ('span#' + case_run_id + '_case_bug_count').text() == '0') {
        jQ('span#' + case_run_id + '_case_bug_count').removeClass('have_bug');
      }
      if (returnobj.run_bug_count == 0) {
        jQ('span#total_run_bug_count').html("<a>No Bugs</a>");
      } else {
        jQ('span#total_run_bug_count a').html("Bugs [" + returnobj.run_bug_count + "]");
      }
      return constructCaseRunZone(container, title_container, case_id);
    } else {
      window.alert(returnobj.response);
      return false;
    }
  };

  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': parameters,
    'success': function(data, textStatus, jqXHR) {
      success(jqXHR);
    },
    'error': function(jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}


function delCaseRun(run_id) {
  var caseruns = serializeCaseRunFromInputList('id_table_cases', 'case_run');
  var numCaseRuns = caseruns.case_run.length;
  if (window.confirm('You are about to delete ' + numCaseRuns + ' case run(s). Are you sure?')) {
    postToURL('removecaserun/', caseruns);
  }
}

function editValue(form,hidebox,selectid,submitid) {
  jQ('#' + hidebox).hide();
  jQ('#' + selectid).show();
  jQ('#' + submitid).show();

  var data = Nitrate.Utils.formSerialize(form);
  var env_property_id = data.env_property_id;

  var success = function(t) {
    var returnobj = jQ.parseJSON(t.responseText);
    var current_value = jQ("input[type=hidden][name=current_run_env]:eq(0)", form);
    var excludeValues = [];
    jQ("input[type=hidden][name=current_run_env]").each(function(index, element) {
      if (element.value != current_value.val()) {
        excludeValues.push(window.parseInt(element.value));
      }
      return true;
    });

    var values = [];
    jQ.each(returnobj, function(index, value){
      if (jQ.inArray(value.pk, excludeValues) < 0) {
        values.push([value.pk, value.fields.value]);
      }
      return true;
    });

    set_up_choices(jQ('#' + selectid)[0], values, 0);
  };

  getInfo({'info_type': 'env_values', 'env_property_id': env_property_id}, success);
}

function submitValue(run_id,value,hidebox,select_field,submitid) {
  var new_value = select_field.options[select_field.selectedIndex].innerHTML;
  var old_value = jQ(select_field).prev().prev().val();

  var dup_values = [];
  jQ("input[type=hidden][name=current_run_env]").each(function(index, element) {
    if (element.value != old_value) {
        dup_values.push(element.value);
    }
    return true;
  });
  if (jQ.inArray(select_field.value, dup_values) >= 0) {
    window.alert("The value is exist for this run");
    return false;
  }

  var success = function(t) {
    var returnobj = jQ.parseJSON(t.responseText);
    if (returnobj.rc == 0) {
      jQ('#' + hidebox).html(new_value).show();
      jQ(select_field).hide();
      jQ('#' + submitid).hide();
      jQ(select_field).prev().prev().val(select_field.value);
    } else {
      window.alert(returnobj.response);
    }
  };

  var failure = function(t) { window.alert("Edit value failed"); };

  var url  = '/runs/env_value/';
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': {'a': 'change', 'old_env_value_id': old_value,
      'new_env_value_id': select_field.value, 'run_id': run_id},
    'success': function(data, textStatus, jqXHR) {
      success(jqXHR);
    },
    'error': function(jqXHR, textStatus, errorThrown) {
      failure();
    }
  });
}

function removeProperty(run_id, element) {
  if (!window.confirm('Are you sure to remove this porperty?')) {
    return false;
  }

  var parent = jQ(element).closest("form");
  var emptySelf = jQ(element).closest("li");
  var env_value_id = jQ("input[type=hidden][name=current_run_env]", parent).get(0).value;

  var success = function(t) {
    var returnobj = jQ.parseJSON(t.responseText);
    if (returnobj.rc == 0) {
      emptySelf.remove();
    } else {
      window.alert(returnobj.response);
    }
  };

  var failure = function(t) { window.alert("Edit value failed"); };
  var url = '/runs/env_value/';
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': {'a': 'remove', 'info_type': 'env_values', 'env_value_id': env_value_id, 'run_id': run_id},
    'success': function(data, textStatus, jqXHR) {
      success(jqXHR);
    },
    'error': function(jqXHR, textStatus, errorThrown) {
      failure();
    }
  });
}

function addProperty(run_id,env_group_id) {
  var template = Handlebars.compile(jQ('#add_property_template').html());
  jQ('#dialog').html(template())
    .find('.js-close-button, .js-cancel-button').bind('click', function() {
      jQ('#dialog').hide();
    })
    .end().show();

  var success = function(t) {
    var returnobj = jQ.parseJSON(t.responseText);
    var values = returnobj.map(function(o) {
      return [o.pk, o.fields.name];
    });

    set_up_choices(jQ('#id_add_env_property')[0], values, 0);
    // load values for the first property in the group. See
    // https://github.com/kiwitcms/Kiwi/issues/142
    change_value(jQ('#id_add_env_property').val(), 'id_add_env_value');
  };

  getInfo({'info_type': 'env_properties', 'env_group_id': env_group_id}, success);

  jQ('#id_add_env_property').bind('change', function(e) {
    change_value(jQ('#id_add_env_property').val(), 'id_add_env_value');
  });

  jQ('#id_env_add').bind('click',function(e) {
    add_property_to_env(run_id, jQ('#id_add_env_value').val());
  });
}

function change_value(env_property_id,selectid) {
  var success = function(t) {
    var returnobj = jQ.parseJSON(t.responseText);
    var values = returnobj.map(function(o) {
      return [o.pk, o.fields.value];
    });

    set_up_choices(jQ('#' + selectid)[0], values, 0);
  };

  getInfo({'info_type': 'env_values', 'env_property_id': env_property_id}, success);
}

function add_property_to_env(run_id, env_value_id) {
  var callback = function(data, textStatus, jqXHR) {
    jQ('#dialog').hide();
    if (data.rc == 0) {
      jQ("#env_area").html(data.fragment);
      jQ('.js-edit-property').bind('click', function() {
        var params = jQ(this).data('params');
        editValue(jQ(this).parents('form.js-run-env')[0], params[0], params[1], params[2]);
      });
      jQ('.js-remove-property').bind('click', function() {
        removeProperty(jQ(this).data('param'), this);
      });
      jQ('.js-env-submit').bind('click', function() {
        var params = jQ(this).data('params');
        submitValue(params[0],params[1],params[2], jQ(this).prev()[0], params[3]);
      });
    } else {
      window.alert(data.response);
    }
  };

  var failure = function(t) { window.alert("Edit value failed"); };
  var url = '/runs/env_value/';
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': {'a': 'add', 'info_type': 'env_values', 'env_value_id':env_value_id, 'run_id': run_id},
    'dataType': 'json',
    'success': callback,
    'error': function (jqXHR, textStatus, errorThrown) {
      failure();
    }
  });
}

function addRunTag(container, run_id) {
  var tag = window.prompt('Please type new tag.');
  if (!tag) {
    return false;
  }

  var url = '/management/tags/';
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': {'a': 'add', 'run': run_id, 'tags': tag},
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
      jQ('.js-remove-tag').bind('click', function() {
        var params = jQ(this).data('params');
        removeRuntag(jQ('.js-tag-ul')[0], params[0], params[1]);
      });
    }
  });
}

function removeRuntag(container, run_id, tag) {
  var url = '/management/tags/';
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': {'a': 'remove', 'run': run_id, 'tags': tag},
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
      jQ('.js-remove-tag').bind('click', function() {
        var params = jQ(this).data('params');
        removeRuntag(jQ('.js-tag-ul')[0], params[0], params[1]);
      });
    }
  });
}

function constructRunCC(container, run_id, parameters) {
  var complete = function(t) {
    jQ('.js-remove-cc').bind('click', function() {
      var params = jQ(this).data('params');
      removeRunCC(params[0], params[1], jQ('.js-cc-ul')[0]);
    });
    if (jQ('#message').length) {
      window.alert(jQ('#message').html());
      return false;
    }
  };
  var url = '/run/' + run_id + '/cc/';
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
    },
    'complete': function() {
      complete();
    }
  });
}

function addRunCC(run_id, container) {
  var user = window.prompt('Please type new email or username for CC.');
  if (!user) {
    return false;
  }
  var parameters = {'do': 'add', 'user': user};
  constructRunCC(container, run_id, parameters);
}

function removeRunCC(run_id, user, container) {
  var c = window.confirm('Are you sure to delete this user from CC?');

  if (!c) {
    return false;
  }

  var parameters = { 'do': 'remove', 'user': user };
  constructRunCC(container, run_id, parameters);
}

function changeCaseRunAssignee() {
  var runs = serializeCaseRunFromInputList(jQ('#id_table_cases')[0]);
  if (!runs.length) {
    window.alert(default_messages.alert.no_case_selected);
    return false;
  }

  var p = window.prompt('Please type new email or username for assignee');
  if (!p) {
    return false;
  }

  jQ.ajax({
    'url': '/run/update-assignee/',
    'type': 'POST',
    'data': { ids: runs, assignee: p },
    'success': function (data, textStatus, jqXHR) {
      window.location.reload();
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

function serializeCaseRunFromInputList(table, name) {
  var elements;
  if (typeof table === 'string') {
    elements = jQ('#' + table).parent().find('input[name="case_run"]:checked');
  } else {
    elements = jQ(table).parent().find('input[name="case_run"]:checked');
  }

  var returnobj_list = [];
  elements.each(function(i) {
    if (typeof this.value === 'string') {
      returnobj_list.push(this.value);
    }
  });
  if (name) {
    var returnobj = {};
    returnobj[name] = returnobj_list;
    return returnobj;
  }

  return returnobj_list;
}

function serialzeCaseForm(form, table, serialized) {
  if (typeof serialized !== 'boolean') {
    var serialized = true;
  }
  var data;
  if (serialized) {
    data = Nitrate.Utils.formSerialize(form);
  } else {
    data = jQ(form).serialize();
  }

  data['case_run'] = serializeCaseFromInputList(table);
  return data;
}

function sortCaseRun(form, order) {
  if (form.order_by.value == order) {
    form.order_by.value = '-' + order;
  } else {
    form.order_by.value = order;
  }
  fireEvent(jQ(form).find('input[type="submit"]')[0], 'click');
}

function showCaseRunsWithSelectedStatus(form, status_id) {
  form.case_run_status__pk.value = status_id;
  fireEvent(jQ(form).find('input[type="submit"]')[0], 'click');
}

//Added for choose runs and add cases to those runs
function serializeRunsFromInputList(table) {
  var elements = jQ('#' + table).parent().find('input[name="run"]:checked');
  var case_ids = [];
  elements.each(function(i) {
    if (typeof this.value === 'string') {
      case_ids.push(this.value);
    }
  });
  return case_ids;
}

function insertCasesIntoTestRun() {
  var answer = window.confirm("Are you sure to add cases to the run?");
  if (!answer) {
    return false;
  }

  var trs = serializeRunsFromInputList("id_table_runs");
  var elements = jQ('[name="case"]');
  var case_ids = [];
  elements.each(function(i) {
    case_ids.push(this.value);
  });

  var data_to_post = {};
  data_to_post['testrun_ids'] = trs;
  data_to_post['case_ids'] = case_ids;

  var url = "../chooseruns/";
  postToURL(url, data_to_post, 'POST');
}

function updateBugsActionAdd(case_runs) {
  var dialog = new AddIssueDialog({
    'extraFormHiddenData': { 'case_runs': case_runs.join() },
    'onSubmit': function(e, dialog) {
      e.stopPropagation();
      e.preventDefault();
      var form_data = dialog.get_data();
      form_data.bug_id = form_data.bug_id.trim();

      if (!form_data.bug_id.length) {
        return;
      }

      if (!validateIssueID(form_data.bug_validation_regexp, form_data.bug_id)) {
        return false;
      }

      jQ.ajax({
        url: '/caserun/update-bugs-for-many/',
        dataType: 'json',
        data: form_data,
        success: function(res){
          if (res.rc === 0) {
            reloadWindow();
          } else {
            window.alert(res.response);
            return false;
          }
        }
      });
    }
  });
  dialog.show();
}

function updateBugsActionRemove(case_runs) {
  var dialog = new AddIssueDialog({
    'action': 'Remove',
    'show_bug_id_field': true,
    'extraFormHiddenData': { 'case_runs': case_runs.join() },
    'onSubmit': function(e, dialog) {
      e.stopPropagation();
      e.preventDefault();
      var form_data = dialog.get_data();
      form_data.bug_id = form_data.bug_id.trim();

      if (!form_data.bug_id.length) {
        return;
      }

      if (!validateIssueID(form_data.bug_validation_regexp, form_data.bug_id)) {
        return false;
      }

      jQ.ajax({
        url: '/caserun/update-bugs-for-many/',
        dataType: 'json',
        success: function(res) {
          if (res.rc == 0) {
            reloadWindow();
          } else {
            window.alert(res.response);
            return false;
          }
        },
        data: form_data,
      });
    }
  });
  dialog.show();
}

function updateBugs(action) {
  var runs = serializeCaseRunFromInputList(jQ('#id_table_cases')[0]);
  if (!runs.length) {
    window.alert(default_messages.alert.no_case_selected);
    return false;
  }

  if (action === "add") {
    updateBugsActionAdd(runs);
  } else if (action === "remove") {
    updateBugsActionRemove(runs);
  } else {
    throw new Error("Unknown operation when update case runs' bugs. This should not happen.");
  }
}

function showCommentForm() {
  var dialog = getDialog();
  var runs = serializeCaseRunFromInputList(jQ('#id_table_cases')[0]);
  if (!runs.length) {
    return window.alert(default_messages.alert.no_case_selected);
  }
  var template = Handlebars.compile(jQ("#batch_add_comment_to_caseruns_template").html());
  jQ(dialog).html(template());

  var commentText = jQ('#commentText');
  var commentsErr = jQ('#commentsErr');
  jQ('#btnComment').live('click', function() {
    var error;
    var comments = jQ.trim(commentText.val());
    if (!comments) {
      error = 'No comments given.';
    }
    if (error) {
      commentsErr.html(error);
      return false;
    }
    jQ.ajax({
      url: '/caserun/comment-many/',
      data: {'comment': comments, 'run': runs.join()},
      dataType: 'json',
      type: 'post',
      success: function(res) {
        if (res.rc == 0) {
          reloadWindow();
        } else {
          commentsErr.html(res.response);
          return false;
        }
      }
    });
  });
  jQ('#btnCancelComment').live('click', function(){
    jQ(dialog).hide();
    commentText.val('');
  });
  jQ(dialog).show();
}

jQ(document).ready(function(){
  jQ('.btnBlueCaserun').mouseover(function() {
    jQ(this).find('ul').show();
  }).mouseout(function() {
    jQ(this).find('ul').hide();
  });
  jQ('ul.statusOptions a').click(function() {
    var option = jQ(this).attr('value');
    var object_pks = serializeCaseRunFromInputList(jQ('#id_table_cases')[0]);
    if (option == '') {
      return false;
    }
    if (!object_pks.length) {
      window.alert(default_messages.alert.no_case_selected);
      return false;
    }
    if (!window.confirm(default_messages.confirm.change_case_status)) {
      return false;
    }
    updateRunStatus(object_pks, option, reloadWindow);
  });
});

function get_addlink_dialog() {
  return jQ('#addlink_dialog');
}

/*
 * Do AJAX request to backend to remove a link
 *
 * - sender: 
 * - link_id: the ID of an arbitrary link.
 */
function removeLink(sender, link_id) {
  jQ.ajax({
    url: '/linkref/remove/' + link_id + '/',
    type: 'GET',
    dataType: 'json',
    success: function(data, textStatus, jqXHR) {
      if (data.rc !== 0) {
        window.alert(data.response);
        return false;
      }
      var li_node = sender.parentNode;
      li_node.parentNode.removeChild(li_node);
    },
    error: function(jqXHR, textStatus, errorThrown) {
      var data = JSON.parse(jqXHR.responseText);
      window.alert(data.message);
    }
  });
}

/*
 * Add link to case run
 *
 * - sender: the Add link button, which is pressed to fire this event.
 * - target_id: to which TestCaseRun the new link will be linked.
 */
function addLinkToCaseRun(sender, case_id, case_run_id) {
  var dialog_p = get_addlink_dialog();

  dialog_p.dialog('option', 'target_id', case_run_id);
  // These two options are used for reloading TestCaseRun when successfully.
  var container = jQ(sender).parents('.case_content.hide')[0];
  dialog_p.dialog('option', 'container', container);
  var title_container = jQ(container).prev()[0];
  dialog_p.dialog('option', 'title_container', title_container);
  dialog_p.dialog('option', 'case_id', case_id);
  dialog_p.dialog('open');
}

/*
 * Initialize dialog for getting information about new link, which is attached
 * to an arbitrary instance of TestCaseRun
 */
function initialize_addlink_dialog() {
  var dialog_p = get_addlink_dialog();

  dialog_p.dialog({
    autoOpen: false,
    modal: true,
    resizable: false,
    height: 300,
    width: 400,
    open: function() {
      jQ(this).unbind('submit').bind('submit', function (e) {
        e.stopPropagation();
        e.preventDefault();
        jQ(this).dialog('widget').find('span:contains("OK")').click();
      });
    },
    buttons: {
      "OK": function() {
        // TODO: validate name and url
        var name = jQ('#testlog_name').attr('value');
        var url = jQ('#testlog_url').attr('value');
        var target_id = jQ(this).dialog('option', 'target_id');

        jQ.ajax({
          url: '/linkref/add/',
          type: 'POST',
          data: { name: name, url: url, target_id: target_id },
          dataType: 'json',
          success: function(data, textStatus, jqXHR) {
            if (data.rc !== 0) {
              window.alert(data.response);
              return false;
            }
            dialog_p.dialog('close');

            // Begin to construct case run area
            var container = dialog_p.dialog('option', 'container');
            var title_container = dialog_p.dialog('option', 'title_container');
            var case_id = dialog_p.dialog('option', 'case_id');
            constructCaseRunZone(container, title_container, case_id);
          },
          error: function (jqXHR, textStatus, errorThrown) {
            var data = JSON.parse(jqXHR.responseText);
            window.alert(data.response);
          }
        });
      },
      "Cancel": function() {
        jQ(this).dialog('close');
      }
    },
    beforeClose: function() {
      // clean name and url for next input
      jQ('#testlog_name').val('');
      jQ('#testlog_url').val('');

      return true;
    },
    /* ATTENTION: target_id can be determined when open this dialog, and
     * this must be set
     */
    target_id: null
  });
}


/*
 * Toggle TestCaseRun panel to edit a case run in run page.
 *
 * Arguments:
 * options.casrunContainer:
 * options.expandPaneContainer:
 * options.caseId:
 * options.caserunId:
 * options.caseTextVersion:
 * options.callback:
 */
function toggleTestCaseRunPane(options) {
  var container = options.caserunRowContainer;
  var content_container = options.expandPaneContainer;
  var callback = options.callback;

  content_container.toggle();

  if (content_container.find('.ajax_loading').length) {
    var url = '/case/' + options.caseId + '/caserun-detail-pane/';
    var data = { case_run_id: options.caserunId, case_text_version: options.caseTextVersion };

    jQ.get(url, data, function(data, textStatus) {
      content_container.html(data);
      callback();
    }, 'html');
  }

  toggleExpandArrow({ caseRowContainer: container, expandPaneContainer: content_container });
}
