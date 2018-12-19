Nitrate.TestCases = {};
Nitrate.TestCases.Details = {};
Nitrate.TestCases.Edit = {};
Nitrate.TestCases.Clone = {};

(function() {
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

function addComponent(component_name) {
    jsonRPC('Component.filter',
            {
                'name': component_name,
                'product_id': Nitrate.TestCases.Instance.product_id
            }, function(data){
                jsonRPC('TestCase.add_component',
                        [Nitrate.TestCases.Instance.pk, data[0].id],
                        function(data) {
                            window.location.reload();
                        }
                );
            }
    );
}

function removeComponent(case_id, component_id) {
    if (! window.confirm(default_messages.confirm.remove_case_component)) {
      return false;
    }

    jsonRPC('TestCase.remove_component', [case_id, component_id], function(data){
        $('#row-' + component_id).hide();
    });
}

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

    // configure autocomplete for components
    jQ('#id_components').autocomplete({
        'source': function(request, response) {
            jsonRPC('Component.filter',
                    {
                        'name__startswith': request.term,
                        'product_id': Nitrate.TestCases.Instance.product_id,
                    }, function(data) {
                        var processedData = [];
                        data.forEach(function(element) {
                            processedData.push(element.name);
                        });
                        response(processedData);
                    }
            );
        },
        'appendTo': '#id_components_autocomplete'
    });

    $('#js-add-component').bind('click', function() {
        addComponent($('#id_components').val());
    });

  jQ('.link_remove_component').bind('click', function(e) {
    removeComponent(Nitrate.TestCases.Instance.pk,
                    jQ('input[name="component"]')[jQ('.link_remove_component').index(this)].value);
  });

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

function configure_product_on_load() {
    $('#id_product').change(function() {
        $('#id_category').find('option').remove();
        update_category_select_from_product();
    });
}

Nitrate.TestCases.Edit.on_load = function() {
    configure_product_on_load();
    if ($('#id_category').val() === null || !$('#id_category').val().length) {
        update_category_select_from_product();
    }

  jQ('.js-back-button').bind('click', function() {
    window.history.go(-1);
  });
};

Nitrate.TestCases.Clone.on_load = function() {
    $('#id_product').change(update_version_select_from_product);
    if (!$('#id_version').val().length) {
        update_version_select_from_product();
    }

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

function changeTestCaseStatus(plan_id, case_ids, new_value, container) {
    case_ids.forEach(function(element) {
        jsonRPC('TestCase.update', [element, {case_status: new_value}], function(data) {});
    });


    var template_type = 'case';
    if (container.attr('id') === 'reviewcases') {
        template_type = 'review_case';
    }

    var parameters = {
        'a': 'initial',
        'from_plan': plan_id,
        'template_type': template_type,
    };

    // todo: #run_case_count, #case_count, #review_case_count
    // are no longer updated
    constructPlanDetailsCasesZone(container, plan_id, parameters);

    Nitrate.TestPlans.Details.reopenTabHelper(jQ(container));
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
      jQ('#testplans_table').DataTable({
        "bFilter": false,
        "bLengthChange": false,
        "bPaginate": false,
        "bInfo": false,
        "bAutoWidth": false,
        "aaSorting": [[ 0, "desc" ]],
        "aoColumns": [
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
