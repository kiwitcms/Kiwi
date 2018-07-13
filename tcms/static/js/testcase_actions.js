Nitrate.TestCases = {};
Nitrate.TestCases.List = {};
Nitrate.TestCases.AdvanceList = {};
Nitrate.TestCases.Details = {};
Nitrate.TestCases.Create = {};
Nitrate.TestCases.Edit = {};
Nitrate.TestCases.Clone = {};

(function() {
  'use restrict';

  var TestCases = window.Nitrate.TestCases || {};

  TestCases.CasesSelection = function(options) {
    this.selectedCasesIds = options.selectedCasesIds || [];
    this.selectAll = options.selectAll;

    if (Object.prototype.toString.call(this.selectedCasesIds) !== '[object Array]') {
      throw new TypeError('selectedCasesIds must an object of Array.');
    }
    if (typeof this.selectAll !== 'boolean') {
      throw new TypeError('selectAll must be a boolean value.');
    }
  };

  TestCases.CasesSelection.prototype.empty = function() {
    return this.selectedCasesIds.length === 0 && !this.selectAll;
  };

  window.Nitrate.TestCases = TestCases;
}());

Nitrate.TestCases.AdvanceList.on_load = function() {
  bind_category_selector_to_product(true, true, jQ('#id_product')[0], jQ('#id_category')[0]);
  bind_component_selector_to_product(true, true, jQ('#id_product')[0], jQ('#id_component')[0]);
  if (jQ('#id_checkbox_all_case').length) {
    jQ('#id_checkbox_all_case').bind('click', function(e) {
      clickedSelectAll(this, jQ(this).closest('form')[0], 'case');
      if (this.checked) {
        jQ('#case_advance_printable').attr('disabled', false);
      } else {
        jQ('#case_advance_printable').attr('disabled', true);
      }
    });
  };

  jQ('#id_blind_all_link').bind('click', function(e) {
    if (!jQ('div[id^="id_loading_"]').length) {
      jQ(this).removeClass('locked');
    }
    if (jQ(this).is('.locked')) {
      //To disable the 'expand all' until all case runs are expanded.
      return false;
    } else {
      jQ(this).addClass('locked');
      var element = jQ(this).children()[0];
      if (jQ(element).is('.collapse-all')) {
        this.title = 'Collapse all cases';
        blinddownAllCases(element);
      } else {
        this.title = 'Expand all cases';
        blindupAllCases(element);
      }
    }
  });

  var toggle_case = function(e) {
    var c = jQ(this).parent()[0]; // Container
    var c_container = jQ(c).next()[0]; // Content Containers
    var case_id = jQ(c).find('input[name="case"]')[0].value;

    toggleTestCasePane({ case_id: case_id, casePaneContainer: jQ(c_container) });
    toggleExpandArrow({ caseRowContainer: jQ(c), expandPaneContainer: jQ(c_container) });
  };

  jQ('.expandable').bind('click', toggle_case);

  jQ("#testcases_table tbody tr input[type=checkbox][name=case]").live('click', function() {
    if (jQ('input[type=checkbox][name=case]:checked').length) {
      jQ("#case_advance_printable").attr('disabled', false);
    } else {
      jQ("#case_advance_printable").attr('disabled', true);
    }
  });

  if (window.location.hash === '#expandall') {
    blinddownAllCases();
  }

  var listParams = Nitrate.TestCases.List.Param;
  jQ('#case_advance_printable').bind('click', function() {
    postToURL(listParams.case_printable, Nitrate.Utils.formSerialize(this.form));
  });
  jQ('#export_selected_cases').bind('click', function() {
    postToURL(listParams.case_export, Nitrate.Utils.formSerialize(this.form));
  });
};

Nitrate.TestCases.List.on_load = function() {
  bind_category_selector_to_product(true, true, jQ('#id_product')[0], jQ('#id_category')[0]);
  bind_component_selector_to_product(true, true, jQ('#id_product')[0], jQ('#id_component')[0]);
  if (jQ('#id_checkbox_all_case')[0]) {
    jQ('#id_checkbox_all_case').bind('click', function(e) {
      clickedSelectAll(this, jQ(this).closest('table')[0], 'case');
      if (this.checked) {
        jQ('#case_list_printable').attr('disabled', false);
      } else {
        jQ('#case_list_printable').attr('disabled', true);
      }
    });
  }

  jQ('#id_blind_all_link').live('click', function(e) {
    if (!jQ('div[id^="id_loading_"]').length) {
      jQ(this).removeClass('locked');
    }
    if (jQ(this).is('.locked')) {
      //To disable the 'expand all' until all case runs are expanded.
      return false;
    } else {
      jQ(this).addClass('locked');
      var element = jQ(this).children()[0];
      if (jQ(element).is('.collapse-all')) {
        this.title = "Collapse all cases";
        blinddownAllCases(element);
      } else {
        this.title = "Expand all cases";
        blindupAllCases(element);
      }
    }
  });

  if (window.location.hash === '#expandall') {
    blinddownAllCases();
  }

  var oTable;
  oTable = jQ('#testcases_table').dataTable({
    "iDisplayLength": 20,
    "sPaginationType": "full_numbers",
    "bFilter": false,
    "bLengthChange": false,
    "aaSorting": [[ 2, "desc" ]],
    "bProcessing": true,
    "bServerSide": true,
    "sAjaxSource": "/cases/ajax/"+this.window.location.search,
    "aoColumns": [
      {"bSortable": false,"sClass": "expandable" },
      {"bSortable": false },
      {"sType": "html","sClass": "expandable"},
      {"sType": "html","sClass": "expandable"},
      {"sType": "html","sClass": "expandable"},
      {"sClass": "expandable"},
      {"sClass": "expandable"},
      {"sClass": "expandable"},
      {"sClass": "expandable"},
      {"sClass": "expandable"},
      {"sClass": "expandable"}
    ]
  });
  jQ("#testcases_table tbody tr td.expandable").live("click", function() {
    var tr = jQ(this).parent();
    var caseRowContainer = tr;
    var case_id = caseRowContainer.find('input[name="case"]').attr('value');
    var detail_td = '<tr class="case_content hide" style="display: none;"><td colspan="11">' +
      '<div id="id_loading_' + case_id + '" class="ajax_loading"></div></td></tr>';
    if (!caseRowContainer.next().hasClass('hide')) {
      caseRowContainer.after(detail_td);
    }

    toggleTestCasePane({ case_id: case_id, casePaneContainer: tr.next() });
    toggleExpandArrow({ caseRowContainer: tr, expandPaneContainer: tr.next() });
  });

  jQ("#testcases_table tbody tr input[type=checkbox][name=case]").live("click", function() {
    if (jQ("input[type=checkbox][name=case]:checked").length) {
      jQ("#case_list_printable").attr('disabled', false);
    } else {
      jQ("#case_list_printable").attr('disabled', true);
    }
  });

  var listParams = Nitrate.TestCases.List.Param;
  jQ('#case_list_printable').bind('click', function() {
    postToURL(listParams.case_printable, Nitrate.Utils.formSerialize(this.form));
  });
  jQ('#export_selected_cases').bind('click', function() {
    postToURL(listParams.case_export, Nitrate.Utils.formSerialize(this.form));
  });
};

Nitrate.TestCases.Details.on_load = function() {
  var case_id = Nitrate.TestCases.Instance.pk;
  constructTagZone(jQ('#tag')[0], { 'case': case_id });
  constructPlanCaseZone(jQ('#plan')[0], case_id);
  jQ('li.tab a').bind('click', function(i) {
    jQ('div.tab_list').hide();
    jQ('li.tab').removeClass('tab_focus');
    jQ(this).parent().addClass('tab_focus');
    jQ('#' + this.title).show();
  });

  if (window.location.hash) {
    fireEvent(jQ('a[href=\"' + window.location.hash + '\"]')[0], 'click');
  }

  jQ('#id_update_component').bind('click', function(e) {
    if (this.diabled) {
      return false;
    }

    var params = {
      'case': Nitrate.TestCases.Instance.pk,
      'product': Nitrate.TestCases.Instance.product_id,
      'category': Nitrate.TestCases.Instance.category_id
    };

    var form_observe = function(e) {
      e.stopPropagation();
      e.preventDefault();

      var params = Nitrate.Utils.formSerialize(this);
      params['case'] = Nitrate.TestCases.Instance.pk;

      var url = Nitrate.http.URLConf.reverse({ name: 'cases_component' });
      var success = function(t) {
        returnobj = jQ.parseJSON(t.responseText);

        if (returnobj.rc === 0) {
          window.location.reload();
        } else {
          window.alert(returnobj.response);
          return false;
        }
      };

      jQ.ajax({
        'url': url,
        'type': 'POST',
        'data': params,
        'traditional': true,
        'success': function (data, textStatus, jqXHR) {
          success(jqXHR);
        },
        'error': function (jqXHR, textStatus, errorThrown) {
          json_failure(jqXHR);
        }
      });
    };

    renderComponentForm(getDialog(), params, form_observe);
  });

  jQ('#id_form_case_component').bind('submit', function(e) {
    e.stopPropagation();
    e.preventDefault();
    var params = Nitrate.Utils.formSerialize(this);
    var submitButton = jQ(this).find(':submit')[0];
    params[submitButton.name] = submitButton.value;
    var parameters = {
      'a': params['a'],
      'case': Nitrate.TestCases.Instance.pk,
      'o_component': params['component']
    };

    if (!parameters['o_component']) {
      return false;
    }

    var c = window.confirm(default_messages.confirm.remove_case_component);
    if (!c) {
      return false;
    }

    updateCaseComponent(this.action, parameters, json_success_refresh_page);
  });

  jQ('.link_remove_component').bind('click', function(e) {
    var c = window.confirm(default_messages.confirm.remove_case_component);
    if (!c) {
      return false;
    }

    var form = jQ('#id_form_case_component')[0];
    var parameters = {
      'a': 'Remove',
      'case': Nitrate.TestCases.Instance.pk,
      'o_component': jQ('input[name="component"]')[jQ('.link_remove_component').index(this)].value
    };
    updateCaseComponent(form.action, parameters, json_success_refresh_page);
  });

  bindSelectAllCheckbox(jQ('#id_checkbox_all_components')[0], jQ('#id_form_case_component')[0], 'component');

  var toggle_case_run = function(e) {
    var c = jQ(this).parent(); // Container
    var c_container = c.next(); // Content Containers
    var case_id = c.find('input[name="case"]')[0].value;
    var case_run_id = c.find('input[name="case_run"]')[0].value;
    // FIXME: case_text_version is not used in the backend to show caserun
    // information, notes, logs, and comments.
    var case_text_version = c.find('input[name="case_text_version"]')[0].value;
    var type = 'case_case_run';
    toggleSimpleCaseRunPane({
      caserunRowContainer: c,
      expandPaneContainer: c_container,
      caseId: case_id,
      caserunId: case_run_id
    });
  };

  var toggle_case_runs_by_plan = function(e) {
    var c = jQ(this).parent();
    var case_id = c.find('input').first().val();
    var params = {
      'type' : 'case_run_list',
      'container': c[0],
      'c_container': c.next()[0],
      'case_id': case_id,
      'case_run_plan_id': c[0].id
    };
    var callback = function(e) {
      jQ('#table_case_runs_by_plan .expandable').bind('click', toggle_case_run);
    };
    toggleCaseRunsByPlan(params, callback);
  };

  jQ('.plan_expandable').bind('click', toggle_case_runs_by_plan);

  jQ('#testplans_table').dataTable({
    "bFilter": false,
    "bLengthChange": false,
    "bPaginate": false,
    "bInfo": false,
    "bAutoWidth": false,
    "aaSorting": [[ 0, "desc" ]],
    "aoColumns": [
      {"sType": "num-html"},
      null,
      {"sType": "html"},
      {"sType": "html"},
      {"sType": "html"},
      null,
      {"bSortable": false}
    ]
  });

  jQ('.js-remove-button').bind('click', function(event) {
    var params = jQ(event.target).data('params');
    removeCaseBug(params.id, params.caseId, params.caseRunId);
  });

  jQ('.js-add-bug').bind('click', function(event) {
    addCaseBug(jQ('#id_case_bug_form')[0]);
  });

  jQ('#id_bugs').bind('keydown', function(event) {
    addCaseBugViaEnterKey(jQ('#id_case_bug_form')[0], event);
  });
};

/*
 * Resize all editors within the webpage after they are rendered.
 * This is used to avoid a bug of TinyMCE in Firefox 11.
 */
function resize_tinymce_editors() {
  jQ('.mceEditor .mceIframeContainer iframe').each(function(item) {
	  var elem = jQ(this);
	  elem.height(elem.height() + 1);
	});
}

Nitrate.TestCases.Create.on_load = function() {
  SelectFilter.init("id_component", "component", 0, "/static/admin/");
  //init category and components
  getCategorisByProductId(false, jQ('#id_product')[0], jQ('#id_category')[0]);
  var from = 'id_component_from';
  var to = 'id_component_to';
  var from_field = jQ('#' + from)[0];
  var to_field = jQ('#' + to)[0];
  jQ(to_field).html('');
  getComponentsByProductId(false, jQ('#id_product')[0], from_field, function() {
    SelectBox.cache[from] = [];
    SelectBox.cache[to] = [];
    for (var i = 0; (node = from_field.options[i]); i++) {
      SelectBox.cache[from].push({value: node.value, text: node.text, displayed: 1});
    }
  });
  // bind change on product to update component and category
  jQ('#id_product').change(function () {
    var from = 'id_component_from';
    var to = 'id_component_to';
    var from_field = jQ('#' + from)[0];
    var to_field = jQ('#' + to)[0];
    jQ(to_field).html('');
    getComponentsByProductId(false, jQ('#id_product')[0], from_field, function() {
      SelectBox.cache[from] = [];
      SelectBox.cache[to] = [];
      for (var i = 0; (node = from_field.options[i]); i++) {
        SelectBox.cache[from].push({value: node.value, text: node.text, displayed: 1});
      }
    });
    getCategorisByProductId(false, jQ('#id_product')[0], jQ('#id_category')[0]);
  });

  resize_tinymce_editors();

  jQ('.js-case-cancel').bind('click', function() {
    window.history.go(-1);
  });
  if (jQ('.js-plan-cancel').length) {
    jQ('.js-plan-cancel').bind('click', function() {
      window.location.href = jQ(this).data('param');
    });
  }
};

Nitrate.TestCases.Edit.on_load = function() {
  bind_category_selector_to_product(false, false, jQ('#id_product')[0], jQ('#id_category')[0]);
  resize_tinymce_editors();

  jQ('.js-back-button').bind('click', function() {
    window.history.go(-1);
  });
};

Nitrate.TestCases.Clone.on_load = function() {
  bind_version_selector_to_product(true);

  jQ('#id_form_search_plan').bind('submit', function(e) {
    e.stopPropagation();
    e.preventDefault();

    var url = '/plans/';
    var container = jQ('#id_plan_container');
    container.show();

    jQ.ajax({
      'url': url,
      'type': 'GET',
      'data': jQ(this).serialize(),
      'success': function (data, textStatus, jqXHR) {
        container.html(data);
      }
    });
  });

  jQ('#id_use_filterplan').bind('click', function(e) {
    jQ('#id_form_search_plan :input').attr('disabled', false);
    jQ('#id_plan_id').val('');
    jQ('#id_plan_id').attr('name', '');
    jQ('#id_copy_case').attr('checked', true);
  });

  if (jQ('#id_use_sameplan').length) {
    jQ('#id_use_sameplan').bind('click', function(e) {
      jQ('#id_form_search_plan :input').attr('disabled', true);
      jQ('#id_plan_id').val(jQ('#value_plan_id').val());
      jQ('#id_plan_id').attr('name', 'plan');
      jQ('#id_plan_container').html('<div class="ajax_loading"></div>').hide();
      jQ('#id_copy_case').attr('checked', false);
    });
  }

  jQ('.js-cancel-button').bind('click', function() {
    window.history.go('-1');
  });

};


/*
 * Used for expanding test case in test plan page specifically
 *
 * Arguments:
 * options.caseRowContainer: a jQuery object referring to the container of the
 *                           test case that is being expanded to show more
 *                           information.
 * options.expandPaneContainer: a jQuery object referring to the container of
 *                              the expanded pane showing test case detail
 *                              information.
 */
function toggleExpandArrow(options) {
  var container = options.caseRowContainer;
  var content_container = options.expandPaneContainer;
  var blind_icon = container.find('img.blind_icon');
  if (content_container.css('display') === 'none') {
    blind_icon.removeClass('collapse').addClass('expand').attr('src', '/static/images/t1.gif');
  } else {
    blind_icon.removeClass('expand').addClass('collapse').attr('src', '/static/images/t2.gif');
  }
}


/*
 * Toggle simple caserun pane in Case Runs tab in case page.
 */
function toggleSimpleCaseRunPane(options) {
  var container = options.caserunRowContainer;
  var content_container = options.expandPaneContainer;
  var caseId = options.caseId;
  var caserunId = options.caserunId;

  content_container.toggle();

  if (container.next().find('.ajax_loading').length) {
    var url = '/case/' + caseId + '/caserun-simple-pane/';
    var data = {case_run_id: caserunId};

    jQ.get(url, data, function(data, textStatus) {
      content_container.html(data);
    },'html');
  }

  toggleExpandArrow({ caseRowContainer: container, expandPaneContainer: content_container });
}

function toggleTestCaseContents(template_type, container, content_container, object_pk, case_text_version, case_run_id, callback) {
  if (typeof container === 'string') {
    var container = jQ('#' + container)[0];
  }

  if(typeof content_container === 'string') {
    var content_container = jQ('#' + content_container)[0];
  }

  jQ(content_container).toggle();

  if (jQ('#id_loading_' + object_pk).length) {
    var url = Nitrate.http.URLConf.reverse({ name: 'case_details', arguments: {id: object_pk} });
    var parameters = {
      template_type: template_type,
      case_text_version: case_text_version,
      case_run_id: case_run_id
    };

    jQ.ajax({
      'url': url,
      'data': parameters,
      'success': function (data, textStatus, jqXHR) {
        jQ(content_container).html(data);
      },
      'error': function (jqXHR, textStatus, errorThrown) {
        html_failure();
      },
      'complete': function (jqXHR, textStatus) {
        callback(jqXHR);
      }
    });
  }

  toggleExpandArrow({ caseRowContainer: jQ(container), expandPaneContainer: jQ(content_container) });
}

function changeTestCaseStatus(plan_id, case_id, new_value, container) {
  var success = function(data, textStatus, jqXHR) {
    var returnobj = jQ.parseJSON(jqXHR.responseText);
    if (returnobj.rc !== 0) {
      window.alert(returnobj.response);
      return false;
    }

    var template_type = 'case';

    if (container.attr('id') === 'reviewcases') {
        template_type = 'review_case';
    }

    var parameters = {
        'a': 'initial',
        'from_plan': plan_id,
        'template_type': template_type,
    };

    constructPlanDetailsCasesZone(container, plan_id, parameters);

    jQ('#run_case_count').text(returnobj.run_case_count);
    jQ('#case_count').text(returnobj.case_count);
    jQ('#review_case_count').text(returnobj.review_case_count);

    Nitrate.TestPlans.Details.reopenTabHelper(jQ(container));
  };

  var data = {
    'from_plan': plan_id,
    'case': case_id,
    'target_field': 'case_status',
    'new_value': new_value,
  };

  jQ.ajax({
    'url': '/ajax/update/case-status/',
    'type': 'POST',
    'data': data,
    'success': success,
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

function toggleAllCheckBoxes(element, container, name) {
  if (element.checked) {
    jQ('#' + container).parent().find('input[name="' + name + '"]').not(':disabled').attr('checked', true);
  } else {
    jQ('#' + container).parent().find('input[name="'+ name + '"]').not(':disabled').attr('checked', false);
  }
}

function toggleAllCases(element) {
  //If and only if both case length is 0, remove the lock.
  if (jQ('div[id^="id_loading_"].normal_cases').length === 0 && jQ('div[id^="id_loading_"].review_cases').length === 0){
    jQ(element).removeClass('locked');
  }

  if (jQ(element).is('.locked')) {
    return false;
  } else {
    jQ(element).addClass('locked');
    if (jQ(element).is('.collapse-all')) {
      element.title = "Collapse all cases";
      blinddownAllCases(element);
    } else {
      element.title = "Expand all cases";
      blindupAllCases(element);
    }
  }
}

function blinddownAllCases(element) {
  jQ('img.expand').each(function(e) {
    fireEvent(this, 'click');
  });
  if (element) {
    jQ(element)
      .removeClass('collapse-all').addClass('expand-all')
      .attr('src', '/static/images/t2.gif');
  }
}

function blindupAllCases(element) {
  jQ('.collapse').each(function(e) {
    fireEvent(this, 'click');
  });

  if (element) {
    jQ(element)
      .removeClass('expand-all').addClass('collapse-all')
      .attr('src', '/static/images/t1.gif');
  }
}

function addCaseBug(form, callback) {
  var addBugInfo = Nitrate.Utils.formSerialize(form);
  addBugInfo.bug_validation_regexp = jQ('select[name="bug_system"] option:selected').data('validation-regexp');
  addBugInfo.bug_id = addBugInfo.bug_id.trim();

  if (!addBugInfo.bug_id.length) {
    // No bug ID input, no any response is required
    return false;
  } else if (!validateIssueID(addBugInfo.bug_validation_regexp, addBugInfo.bug_id)) {
    return false;
  }

  var complete = function(t) {
    jQ('.js-add-bug').bind('click', function(event) {
      addCaseBug(jQ('#id_case_bug_form')[0]);
    });
    jQ('#id_bugs').bind('keydown', function(event) {
      addCaseBugViaEnterKey(jQ('#id_case_bug_form')[0], event);
    });
    jQ('.js-remove-button').bind('click', function(event) {
      var params = jQ(event.target).data('params');
      removeCaseBug(params.id, params.caseId, params.caseRunId);
    });
    if (jQ('#response').length) {
      window.alert(jQ('#response').html());
      return false;
    }

    if (callback) {
      callback();
    }
    jQ('#case_bug_count').text(jQ('table#bugs').attr('count'));
  };

  jQ.ajax({
    'url': form.action,
    'type': form.method,
    'data': addBugInfo,
    'success': function (data, textStatus, jqXHR) {
      jQ('#bug_list').html(data);
    },
    'complete': function () {
      complete();
    }
  });
}

function removeCaseBug(id, case_id, case_run_id) {
  if(!window.confirm('Are you sure to remove the bug?')) {
    return false;
  }

  var parameteres = { 'handle': 'remove', 'id': id, 'run_id': case_run_id };

  var complete = function(t) {
    jQ('.js-remove-button').bind('click', function(event) {
      var params = jQ(event.target).data('params');
      removeCaseBug(params.id, params.caseId, params.caseRunId);
    });
    jQ('.js-add-bug').bind('click', function(event) {
      addCaseBug(jQ('#id_case_bug_form')[0]);
    });
    jQ('#id_bugs').bind('keydown', function(event) {
      addCaseBugViaEnterKey(jQ('#id_case_bug_form')[0], event);
    });

    if (jQ('#response').length) {
      window.alert(jQ('#response').html());
      return false;
    }
    jQ('#case_bug_count').text(jQ('table#bugs').attr('count'));
  };

  jQ.ajax({
    'url': '/case/' + case_id + '/bug/',
    'type': 'GET',
    'data': parameteres,
    'success': function (data, textStatus, jqXHR) {
      jQ('#bug_list').html(data);
    },
    'complete': function () {
      complete();
    }
  });
}

function constructPlanCaseZone(container, case_id, parameters) {
  var complete = function(t) {
    jQ('#id_plan_form').bind('submit', function(e) {
      e.stopPropagation();
      e.preventDefault();

      var callback = function(e) {
        e.stopPropagation();
        e.preventDefault();
        var plan_ids = Nitrate.Utils.formSerialize(this)['plan_id'];
        if (!plan_ids) {
          window.alert(default_messages.alert.no_plan_specified);
          return false;
        }

        var p = { a: 'add', plan_id: plan_ids };
        constructPlanCaseZone(container, case_id, p);
        clearDialog();
        jQ('#plan_count').text(jQ('table#testplans_table').attr('count'));
      };

      var p = Nitrate.Utils.formSerialize(this);
      if (!p.pk__in) {
        window.alert(default_messages.alert.no_plan_specified);
        return false;
      }

      var action_url = Nitrate.http.URLConf.reverse({ name: 'case_plan', arguments: {id: case_id} });
      previewPlan(p, action_url, callback);
    });
    if (jQ('#testplans_table td a').length) {
      jQ('#testplans_table').dataTable({
        "bFilter": false,
        "bLengthChange": false,
        "bPaginate": false,
        "bInfo": false,
        "bAutoWidth": false,
        "aaSorting": [[ 0, "desc" ]],
        "aoColumns": [
          {"sType": "num-html"},
          null,
          {"sType": "html"},
          {"sType": "html"},
          {"sType": "html"},
          null,
          {"bSortable": false}
        ]
      });
    }

    jQ('.js-remove-plan').bind('click', function() {
      var params = jQ(this).data('params');
      removePlanFromCase(jQ('#testplans_table_wrapper')[0], params[0], params[1]);
    });

  };

  var url = Nitrate.http.URLConf.reverse({ name: 'case_plan', arguments: {id: case_id} });

  jQ.ajax({
    'url': url,
    'type': 'GET',
    'data': parameters,
    'traditional': true,
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
    },
    'complete': function (jqXHR, textStatus, errorThrown) {
      complete();
    }
  });
}

function removePlanFromCase(container, plan_id, case_id) {
  var c = window.confirm('Are you sure to remove the case from this plan?');
  if (!c) {
    return false;
  }
  var parameters = { a: 'remove', plan_id: plan_id };
  constructPlanCaseZone(container, case_id, parameters);
  jQ('#plan_count').text(jQ('table#testplans_table').attr('count'));
}

function renderComponentForm(container, parameters, form_observe) {
  var d = jQ('<div>');
  if (!container) {
    var container = getDialog();
  }
  jQ(container).show();

  var callback = function(t) {
    var action = Nitrate.http.URLConf.reverse({ name: 'cases_component' });
    var notice = 'Press "Ctrl" to select multiple default component';
    var h = jQ('<input>', {'type': 'hidden', 'name': 'a', 'value': 'add'});
    var a = jQ('<input>', {'type': 'submit', 'value': 'Add'});
    var c = jQ('<label>');
    c.append(h);
    c.append(a);
    a.bind('click', function(e) { h.val('add'); });
    var f = constructForm(d.html(), action, form_observe, notice, c[0]);
    jQ(container).html(f);
    bind_component_selector_to_product(false, false, jQ('#id_product')[0], jQ('#id_o_component')[0]);
  };

  var url = Nitrate.http.URLConf.reverse({ name: 'cases_component' });

  jQ.ajax({
    'url': url,
    'type': 'POST',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      d.html(data);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      html_failure();
    },
    'complete': function() {
      callback();
    }
  });
}


function renderCategoryForm(container, parameters, form_observe) {
  var d = jQ('<div>');
  if (!container) {
    var container = getDialog();
  }
  jQ(container).show();

  var callback = function(t) {
    var action = Nitrate.http.URLConf.reverse({ name: 'cases_category' });
    var notice = 'Select Category';
    var h = jQ('<input>', {'type': 'hidden', 'name': 'a', 'value': 'add'});
    var a = jQ('<input>', {'type': 'submit', 'value': 'Select'});
    var c = jQ('<label>');
    c.append(h);
    c.append(a);
    a.bind('click', function(e) { h.val('update'); });
    var f = constructForm(d.html(), action, form_observe, notice, c[0]);
    jQ(container).html(f);
    bind_category_selector_to_product(false, false, jQ('#id_product')[0], jQ('#id_o_category')[0]);
  };

  var url = Nitrate.http.URLConf.reverse({ name: 'cases_category' });

  jQ.ajax({
    'url': url,
    'type': 'POST',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      d.html(data);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      html_failure();
    },
    'complete': function() {
      callback();
    }
  });
}

// FIXME: this
function updateCaseComponent(url, parameters, callback) {
  jQ.ajax({
    'url': url,
    'type': 'POST',
    'data': parameters,
    'traditional': true,
    'success': function (data, textStatus, jqXHR) {
      callback(jqXHR);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

// FIXME: this, and other code that calls Ajax.Request
function updateCaseCategory(url, parameters, callback) {
  jQ.ajax({
    'url': url,
    'type': 'POST',
    'data': parameters,
    'success': function (data, textStatus, jqXHR) {
      callback(jqXHR);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}

function constructCaseAutomatedForm(container, callback, options) {
  jQ(container).html(getAjaxLoading());
  jQ(container).show();

  var d = jQ('<div>', { 'class': 'automated_form' })[0];
  var create_form_cb = function(t) {
    var returntext = t.responseText;
    var action = '/cases/automated/';
    var form_observe = function(e) {
      e.stopPropagation();
      e.preventDefault();

      if (!jQ(this).find('input[type="checkbox"]:checked').length) {
        window.alert('Nothing selected');
        return false;
      }

      var params = serializeFormData({
        form: this,
        zoneContainer: options.zoneContainer,
        casesSelection: options.casesSelection
      });
      /*
       * Have to add this. The form generated before does not contain a
       * default value `change'. In fact, the field a must contain the
       * only value `change', here.
       */
      params = params.replace(/a=\w*/, 'a=change');
      var url = Nitrate.http.URLConf.reverse({ name: 'cases_automated' });
      jQ.ajax({
        'url': url,
        'type': 'POST',
        'data': params,
        'success': function (data, textStatus, jqXHR) {
          callback(jqXHR);
        }
      });
    };
    var f = constructForm(returntext, action, form_observe);
    jQ(container).html(f);
  };


  // load the HTML form
  jQ.ajax({
    'url': '/cases/form/automated/',
    'type': 'GET',
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      window.alert('Getting form get errors');
      return false;
    },
    'complete': function(jqXHR) {
      create_form_cb(jqXHR);
    }
  });
}

/*
 * Serialize selected cases' Ids.
 *
 * This function inherits the ability from original definition named
 * serializeCaseFromInputList, except that it also collects whehter all cases
 * are also selected even through not all of cases are displayed.
 *
 * Return value is an object of dictionary holding two properties. `selectAll'
 * is a boolean value indicating whether user select all cases.
 * `selectedCasesIds' is an array containing all selected cases' Ids the
 * current loaded set of cases.
 *
 * Whatever user selects all cases, above two properties appears always with
 * proper value.
 */
function serializeCaseFromInputList2(table) {
  var selectAll = jQ(table).parent().find('.js-cases-select-all input[type="checkbox"]')[0].checked;
  var case_ids = [];
  var checkedCases = jQ(table).find('input[name="case"]:checked');
  checkedCases.each(function(i, checkedCase) {
    if (typeof checkedCase.value === 'string') {
      case_ids.push(checkedCase.value);
    }
  });
  var selectedCasesIds = case_ids;

  return new Nitrate.TestCases.CasesSelection({
    selectedCasesIds: selectedCasesIds,
    selectAll: selectAll
  });
}

function serializeCaseFromInputList(table) {
  var case_ids = [];
  jQ(table).parent().find('input[name="case"]:checked').each(function(i) {
    if (typeof this.value === 'string') {
      case_ids.push(this.value);
    }
  });
  return case_ids;
}

/*
 * Serialize criterias for searching cases.
 *
 * Arguments:
 * - form: the form from which criterias are searched
 * - table: the table containing all loaded cases
 * - serialized: whether to serialize the form data. true is default, if not
 *   passed.
 * - exclude_cases: whether to exclude all cases while serializing. For
 *   instance, when filter cases, it's unnecessary to collect all selected
 *   cases' IDs, due to all filtered cases in the response should be selected
 *   by default. Default to true if not passed.
 */
function serialzeCaseForm(form, table, serialized, exclude_cases) {
  if (typeof serialized != 'boolean') {
    var serialized = true;
  }
  if (exclude_cases === undefined) {
    var exclude_cases = false;
  }
  var data;
  if (serialized) {
    data = Nitrate.Utils.formSerialize(form);
  } else {
    data = jQ(form).serialize();
  }

  if (!exclude_cases) {
    data['case'] = serializeCaseFromInputList(table);
  }
  return data;
}

/*
 * New implementation of serialzeCaseForm to allow to choose whether the
 * TestCases' Ids are necessary to be serialized.
 *
 * Be default if no value is passed to exclude_cases, not exclude them.
 */
function serializeCaseForm2(form, table, serialized, exclude_cases) {
  if (typeof serialized != 'boolean') {
    var serialized = true;
  }
  var data;
  if (serialized) {
    data = Nitrate.Utils.formSerialize(form);
  } else {
    data = jQ(form).serialize();
  }
  var _exclude = exclude_cases === undefined ? false : exclude_cases;
  if (!_exclude) {
    data['case'] = serializeCaseFromInputList(table);
  }
  return data;
}

function toggleDiv(link, divId) {
  var link = jQ(link);
  var div = jQ('#' + divId);
  var show = 'Show All';
  var hide = 'Hide All';
  div.toggle();
  var text = link.html();
  if (text !== show) {
    link.html(show);
  } else {
    link.html(hide);
  }
}

function addCaseBugViaEnterKey(element, e) {
  if (e.keyCode == 13) {
    addCaseBug(element);
  }
}

function toggleCaseRunsByPlan(params, callback) {
  var container = params.container;
  var content_container = params.c_container;
  var case_run_plan_id = params.case_run_plan_id;
  var case_id = params.case_id;
  if (typeof container === 'string') {
    container = jQ('#' + container);
  } else {
    container = jQ(container);
  }

  if(typeof content_container === 'string') {
    content_container = jQ('#' + content_container);
  } else {
    content_container = jQ(content_container);
  }

  content_container.toggle();

  if (jQ('#id_loading_' + case_run_plan_id).length) {
    var url = '/case/' + case_id + '/caserun-list-pane/';
    var parameters = { plan_id: case_run_plan_id };

    jQ.ajax({
      'url': url,
      'type': 'GET',
      'data': parameters,
      'success': function (data, textStatus, jqXHR) {
        content_container.html(data);
      },
      'error': function (jqXHR, textStatus, errorThrown) {
        html_failure();
      },
      'complete': function() {
        callback();
      }
    });

  }

  var blind_icon = container.find('img').first();
  if (content_container.is(':hidden')) {
    blind_icon.removeClass('collapse').addClass('expand').attr('src', '/static/images/t1.gif');
  } else {
    blind_icon.removeClass('expand').addClass('collapse').attr('src', '/static/images/t2.gif');
  }
}
