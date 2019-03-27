Nitrate.TestCases = {};
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
