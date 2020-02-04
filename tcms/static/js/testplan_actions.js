Nitrate.TestPlans = {};
Nitrate.TestPlans.Details = {};
Nitrate.TestPlans.SearchCase = {};

/*
 * Hold container IDs
 */
Nitrate.TestPlans.CasesContainer = {
  // containing cases with confirmed status
  ConfirmedCases: 'testcases',
  // containing cases with non-confirmed status
  ReviewingCases: 'reviewcases'
};


Nitrate.TestPlans.TreeView = {
  'pk': new Number(),
  'data': {},
  'tree_elements': jQ('<div>')[0],
  'default_container': 'id_tree_container',
  'default_parameters': { t: 'ajax' }, // FIXME: Doesn't make effect here.
  'filter': function(parameters, callback) {
    jsonRPC('TestPlan.filter', parameters, callback, true);
  },
  'init': function(plan_id) {
    // Current, Parent, Brothers, Children, Temporary current
    var c_plan, p_plan, b_plans, ch_plans, tc_plan;

    // Get the current plan
    var p1 = {pk: plan_id};
    var c1 = function(returnobj) {
      if (returnobj.length) {
        c_plan = returnobj[0];
      }
    };
    this.filter(p1, c1);
    if (!c_plan) {
      window.alert('Plan ' + plan_id + ' can not found in database');
      return false;
    }

    // Get the parent plan
    if (c_plan.parent) {
      var p2 = { pk: c_plan.parent_id};
      var c2 = function(returnobj) {
        p_plan = returnobj[0];
      };
      this.filter(p2, c2);
    }

    // Get the brother plans
    if (c_plan.parent) {
      var p3 = { parent: c_plan.parent_id};
      var c3 = function(returnobj) {
        b_plans = returnobj;
      };
      this.filter(p3, c3);
    }

    // Get the child plans
    var p4 = { parent: c_plan.id};
    var c4 = function(returnobj) {
      ch_plans = returnobj;
    };
    this.filter(p4, c4);

    // Combine all of plans
    // Presume the plan have parent and brother at first
    if (p_plan && b_plans) {
      p_plan.children = b_plans;
      tc_plan = this.traverse(p_plan.children, c_plan.id);
      tc_plan.is_current = true;
      if (ch_plans) {
        tc_plan.children = ch_plans;
      }

      if (p_plan.id) {
        p_plan = Nitrate.Utils.convert('obj_to_list', p_plan);
      }

      this.data = p_plan;
    } else {
      c_plan.is_current = true;
      if (ch_plans) {
        c_plan.children = ch_plans;
      }
      this.data = Nitrate.Utils.convert('obj_to_list', c_plan);
    }
  },
  'blind': function(e) {
    var e_container = this;
    var li_container = jQ(e_container).parent().parent();
    var container_clns = jQ(e_container).attr('class').split(/\s+/);
    var expand_icon_url = '/static/images/t2.gif';
    var collapse_icon_url = '/static/images/t1.gif';

    container_clns.forEach(function(className, index) {
      if (typeof className === 'string') {
        switch (className) {
          case 'expand_icon':
            li_container.find('ul').eq(0).hide();
            e_container.src = collapse_icon_url;
            jQ(e_container).removeClass('expand_icon');
            jQ(e_container).addClass('collapse_icon');
            break;

          case 'collapse_icon':
            li_container.find('ul').eq(0).show();
            e_container.src = expand_icon_url;
            jQ(e_container).removeClass('collapse_icon');
            jQ(e_container).addClass('expand_icon');
            break;
        }
      }
    });
  },
  'render': function(data) {
    var ul = jQ('<ul>');
    var icon_expand = '<img src="/static/images/t2.gif" class="expand_icon js-toggle-icon">';
    var icon_collapse = '<img src="/static/images/t1.gif" class="collapse_icon js-toggle-icon">';

    if (!data && this.data) {
      var data = this.data;
    }

    // Add the child plans to parent
    for (var i in data) {
      if (!data[i].id) {
        continue;
      }

      var li = jQ('<li>');
      var title = '[<a href="/plan/' + data[i].id + '/">' + data[i].id + '</a>] ';


      if (data[i].children) {
        title = icon_expand + title;
        li.addClass('no-list-style');
      } else {
        li.addClass('no-list-style');
      }

      if (data[i].is_current) {
        li.addClass('current');
      }

      if (data[i].is_active) {
        title = '<div>' + title;
      } else {
        title = '<div class="line-through">' + title;
      }

      // Construct the items
      title += '<a class="plan_name" href="/plan/' + data[i].id + '/">' + data[i].name + '</a>';
      title += '</div>';

      li.html(title);
      ul.append(li);

      // Observe the blind link click event
      // li[0].adjacent('img').invoke('observe', 'click', this.blind);
      li.find('.js-toggle-icon').bind('click', this.blind);
      if (data[i].children) {
        li.append(this.render(data[i].children));
      }
    }

    return ul[0];
  },
  'render_page': function(container) {
    var _container = container || this.default_container;
    jQ('#' + _container).html(getAjaxLoading());
    jQ('#' + _container).html(this.render());
  },
  'traverse': function(data, pk) {
    // http://stackoverflow.com/questions/3645678/javascript-get-a-reference-from-json-object-with-traverse
    for (i in data) {
      if (data[i] == [] || typeof data[i] != 'object') {
        continue;
      }

      if (data[i].id === pk) {
        return data[i];
      }

      if (typeof data[i].children === 'object') {
        var retVal = this.traverse(data[i].children, pk);
        if (typeof retVal != 'undefined') {
          return retVal;
        }
      }
    }
  },
  'insert': function(node, data) {
    if (node.children) {
      return node;
    }

    node.children = data;
    return node;
  },
  'toggleRemoveChildPlanButton': function() {
    var treeContainer = jQ('#' + Nitrate.TestPlans.TreeView.default_container);
    var tvTabContainer = Nitrate.TestPlans.Details.getTabContentContainer({
      containerId: Nitrate.TestPlans.Details.tabContentContainerIds.treeview
    });
    var toEnableRemoveButton = treeContainer.find('.current').find('ul li').length > 0;
    if (toEnableRemoveButton) {
      tvTabContainer.find('.remove_node')[0].disabled = false;
    } else {
      tvTabContainer.find('.remove_node')[0].disabled = true;
    }
  },
  'updateChildPlan': function(container, current_plan_id, plan_id, plan_id_type) {
    var self = this;
    var childPlanIds = window.prompt('Enter a comma separated list of plan IDs');
    if (!childPlanIds) {
      return false;
    }

    var callback = function(e) {
      e.stopPropagation();
      e.preventDefault();
      var cbUpdateTreeView = function(t) {
        clearDialog();
        var planDetails = Nitrate.TestPlans.Details;
        var container = planDetails.getTabContentContainer({
          containerId: planDetails.tabContentContainerIds.treeview
        });
        planDetails.loadPlansTreeView(current_plan_id);
        self.toggleRemoveChildPlanButton();
      };

      jQ.ajax({
        'url': '/plan/update-parent/',
        'type': 'POST',
        'data': { child_ids: childPlanIds.split(','), parent_id: plan_id },
        'success': function (data, textStatus, jqXHR) {
          cbUpdateTreeView(jqXHR);
        },
        'error': function (jqXHR, textStatus, errorThrown) {
          json_failure(jqXHR);
        }
      });
    };

    previewPlan(childPlanIds, '', callback);
  },
};

Nitrate.TestPlans.Details = {
  'tabContentContainerIds': {
    'document': 'document',
    'confirmedCases': 'testcases',
    'reviewingCases': 'reviewcases',
    'attachment': 'attachment',
    'testruns': 'testruns',
    'log': 'log',
    'treeview': 'treeview',
    'tag': 'tag'
  },
  'getTabContentContainer': function(options) {
    var containerId = options.containerId;
    var constants = Nitrate.TestPlans.Details.tabContentContainerIds;
    var id = constants[containerId];
    if (id === undefined) {
      return undefined;
    } else {
      return jQ('#' + id);
    }
  },
  /*
   * Lazy-loading TestPlans TreeView
   */
  'loadPlansTreeView': function(plan_id) {
    // Initial the tree view
    Nitrate.TestPlans.TreeView.init(plan_id);
    Nitrate.TestPlans.TreeView.render_page();
  },
  'initTabs': function() {
    jQ('li.tab a').bind('click', function(i) {
      jQ('div.tab_list').hide();
      jQ('li.tab').removeClass('tab_focus');
      jQ(this).parent().addClass('tab_focus');
      jQ('#' + this.href.slice(this.href.indexOf('#') + 1)).show();
    });

    // Display the tab indicated by hash along with URL.
    var defaultSwitchTo = '#testcases';
    var switchTo = window.location.hash;
    var exist = jQ('#contentTab')
      .find('a')
      .map(function(index, element) {
        return element.getAttribute('href');
      })
      .filter(function(index, element) {
        return element === switchTo;
      }).length > 0;
    if (!exist) {
      switchTo = defaultSwitchTo;
    }
    fireEvent(jQ('a[href=\"' + switchTo + '\"]')[0], 'click');
  },
  /*
   * Load cases table.
   *
   * Proxy of global function with same name.
   */
  'loadCases': function(container, plan_id, parameters) {
    constructPlanDetailsCasesZone(container, plan_id, parameters);

    if (Nitrate.TestPlans.Details._bindEventsOnLoadedCases === undefined) {
      Nitrate.TestPlans.Details._bindEventsOnLoadedCases = bindEventsOnLoadedCases({
        'cases_container': container,
        'plan_id': plan_id,
        'parameters': parameters
      });
    }
  },
  // Loading newly created cases with proposal status to show table of these kind of cases.
  'loadConfirmedCases': function(plan_id) {
    var params = { 'a': 'initial', 'template_type': 'case', 'from_plan': plan_id };
    var container = Nitrate.TestPlans.CasesContainer.ConfirmedCases;
    Nitrate.TestPlans.Details.loadCases(container, plan_id, params);
  },
  // Loading reviewing cases to show table of these kind of cases.
  'loadReviewingCases': function(plan_id) {
    var params = { 'a': 'initial', 'template_type': 'review_case', 'from_plan': plan_id };
    var container = Nitrate.TestPlans.CasesContainer.ReviewingCases;
    Nitrate.TestPlans.Details.loadCases(container, plan_id, params);
  },
  'bindEventsOnLoadedCases': function(container) {
    var elem;
    if (typeof container === 'string') {
      elem = jQ('#' + container);
    } else {
      elem = jQ(container);
    }
    var form = elem.children()[0];
    var table = elem.children()[1];
    Nitrate.TestPlans.Details._bindEventsOnLoadedCases(table, form);
  },
  /*
   * No more cases to load.
   *
   * Arguments:
   * - container: a jQuery object. Representing current Cases or Revieiwng Cases tab.
   */
  'noMoreToLoad': function(container) {
    var countInfo = Nitrate.TestPlans.Details.getLoadedCasesCountInfo(container);
    return countInfo.remaining === 0;
  },
  /*
   * Get cases count information.
   *
   * Getting all these information relies on the HTML element within page. No
   * any interaction with backend.
   */
  'getLoadedCasesCountInfo': function(container) {
    var contentContainer = container;
    var casesListContainer = contentContainer.find('.js-cases-list');
    var totalCasesCount = contentContainer
      .find('.js-remaining-cases-count').attr('data-cases-count');
    var loadedCasesCount = casesListContainer.find('tr[id]').length;
    var remainingCount = parseInt(totalCasesCount) - parseInt(loadedCasesCount);
    return { 'loaded': loadedCasesCount, 'remaining': remainingCount };
  },
  /*
   * Show the remaining number of TestCases to be loaded.
   *
   * A side-effect is that when there is no more TestCases to be loaded,
   * disable Show More hyperlink and display descriptive text to tell user
   * what is happening.
   */
  showRemainingCasesCount: function(container) {
    var contentContainer = jQ('#' + container);
    var countInfo = Nitrate.TestPlans.Details.getLoadedCasesCountInfo(contentContainer);
    var noMoreToLoad = Nitrate.TestPlans.Details.noMoreToLoad(contentContainer);
    contentContainer.find('.js-number-of-loaded-cases').text(countInfo.loaded);
    if (noMoreToLoad) {
      contentContainer.find('a.js-load-more').die('click').toggle();
      contentContainer.find('span.js-loading-progress').toggle();
      contentContainer.find('span.js-nomore-msg').toggle();
      setTimeout(function() {
        contentContainer.find('span.js-nomore-msg').toggle('slow');
      }, 2000);
    } else {
      contentContainer.find('.js-remaining-cases-count').text(countInfo.remaining);
    }
  },
  // The real function to load more cases and show them in specific container.
  'loadMoreCasesClicHandler': function(e, container) {
    var elemLoadMore = jQ('#' + container).find('.js-load-more');
    var post_data = elemLoadMore.attr('data-criterias');
    var page_index = elemLoadMore.attr('data-page-index');
    var page_index_re = /page_index=\d+/;
    if (post_data.match(page_index_re)) {
      post_data = post_data.replace(page_index_re, 'page_index=' + page_index);
    } else {
      post_data = post_data + '&page_index=' + page_index;
    }

    jQ('#' + container).find('.ajax_loading').show();

    jQ.post('/cases/load-more/', post_data, function(data) {
      var has_more = jQ(data)[0].hasAttribute('id');
      if (has_more) {
        jQ('#' + container).find('.ajax_loading').hide();

        var casesListContainer = jQ('#' + container).find('.js-cases-list');
        casesListContainer.find('tbody:first').append(data);

        // Increase page index for next batch cases to load
        var page_index = elemLoadMore.attr('data-page-index');
        elemLoadMore.attr('data-page-index', parseInt(page_index) + 1);

        Nitrate.TestPlans.Details.bindEventsOnLoadedCases(container);

        // Calculate the remaining number of cases
        Nitrate.TestPlans.Details.showRemainingCasesCount(container);
        Nitrate.TestPlans.Details.toggleSelectAllInput(jQ('#' + container));
      } else {
        elemLoadMore.unbind('click').remove();
      }
    }).fail(function() {
      jQ('#' + container).find('.ajax_loading').hide();
      window.alert('Cannot load subsequent cases.');
    });
  },
  // Load more cases with previous criterias.
  'onLoadMoreCasesClick': function(e) {
    var container = Nitrate.TestPlans.CasesContainer.ConfirmedCases;
    Nitrate.TestPlans.Details.loadMoreCasesClicHandler(e, container);
  },
  // Load more reviewing cases with previous criterias.
  'onLoadMoreReviewcasesClick': function(e) {
    var container = Nitrate.TestPlans.CasesContainer.ReviewingCases;
    Nitrate.TestPlans.Details.loadMoreCasesClicHandler(e, container);
  },
  'observeLoadMore': function(container) {
    var NTC = Nitrate.TestPlans.CasesContainer;
    var NTD = Nitrate.TestPlans.Details;
    var loadMoreEventHandlers = {};
    loadMoreEventHandlers[NTC.ConfirmedCases] = NTD.onLoadMoreCasesClick;
    loadMoreEventHandlers[NTC.ReviewingCases] = NTD.onLoadMoreReviewcasesClick;
    var eventHandler = loadMoreEventHandlers[container];
    if (eventHandler) {
      jQ('#' + container).find('.js-load-more').die('click').live('click', eventHandler);
    }
  },
  'observeEvents': function(plan_id) {
    var NTPD = Nitrate.TestPlans.Details;

    jQ('#tab_testcases').bind('click', function(e) {
      if (!NTPD.testcasesTabOpened) {
        NTPD.loadConfirmedCases(plan_id);
        NTPD.testcasesTabOpened = true;
      };
    });

    jQ('#tab_treeview').bind('click', function(e) {
      if (!NTPD.plansTreeViewOpened) {
        NTPD.loadPlansTreeView(plan_id);
        NTPD.plansTreeViewOpened = true;
      }
    });

    jQ('#tab_reviewcases').bind('click', function(e) {
      var opened  = Nitrate.TestPlans.Details.reviewingCasesTabOpened;
      if (!opened) {
        Nitrate.TestPlans.Details.loadReviewingCases(plan_id);
        Nitrate.TestPlans.Details.reviewingCasesTabOpened = true;
      }
    });
  },
  'reopenCasesTabThen': function() {
    Nitrate.TestPlans.Details.testcasesTabOpened = false;
  },
  'reopenReviewingCasesTabThen': function() {
    Nitrate.TestPlans.Details.reviewingCasesTabOpened = false;
  },
  /*
   * Show or hide the input control for Select All.
   *
   * Arguments:
   * - container: a jQuery object. Representing current Cases or Revieiwng Cases tab.
   */
  'toggleSelectAllInput': function(container) {
    var uncheckedCaseIdExists = container.find('.js-cases-list')
      .find('input[name="case"]:not(:checked)').length > 0;
    var noMoreCasesToLoad = Nitrate.TestPlans.Details.noMoreToLoad(container);

    var selectAllDiv = container.find('.js-cases-select-all');
    if (uncheckedCaseIdExists || noMoreCasesToLoad) {
      selectAllDiv.hide();
      selectAllDiv.find('input[type="checkbox"]')[0].checked = false;
    } else {
      selectAllDiv.show();
      selectAllDiv.find('input[type="checkbox"]')[0].checked = true;
    }
  },
  /*
   * Uncheck select all loaded cases if any case is unchecked, or check it otherwise.
   *
   * Argument:
   * - container: a jQuery object. Representing current Cases or Reviewing Cases tab.
   */
  'refreshCasesSelectionCheck': function(container) {
    var casesMostCloseContainer = container.find('.js-cases-list');
    var notSelectAll = casesMostCloseContainer.find('input[name="case"]:not(:checked)').length > 0;
    casesMostCloseContainer.find('input[value="all"]')[0].checked = !notSelectAll;

    Nitrate.TestPlans.Details.toggleSelectAllInput(container);
  },
  /*
   * Helper function to reopen other tabs.
   *
   * Arguments:
   * - container: a jQuery object, where the operation happens to reopen other tabs. The container
   *              Id is used to select the reopen operations.
   */
  'reopenTabHelper': function(container) {
    var switchMap = {
      'testcases': function() { Nitrate.TestPlans.Details.reopenReviewingCasesTabThen(); },
      'reviewcases': function() { Nitrate.TestPlans.Details.reopenCasesTabThen(); }
    };
    switchMap[container.attr('id')]();
  },
  'on_load': function() {
    var plan_id = Nitrate.TestPlans.Instance.pk;

    // Initial the contents
    constructTagZone(jQ('#tag')[0], { plan: plan_id });

    Nitrate.TestPlans.Details.observeEvents(plan_id);
    Nitrate.TestPlans.Details.initTabs();

    jQ('#btn_edit, #btn_delete').bind('click', function() {
      window.location.href = jQ(this).data('param');
    });
    jQ('#btn_clone, #btn_print').bind('click', function() {
      var params = jQ(this).data('params');
      postToURL(params[0], {'plan': params[1]});
    });
    var treeview = jQ('#treeview')[0];
    var planPK = jQ('#id_tree_container').data('param');
    jQ('#js-add-child-node').bind('click', function() {
      Nitrate.TestPlans.TreeView.updateChildPlan(treeview, planPK, planPK, 'int');
    });
    jQ('#js-remove-child-node').bind('click', function() {
      Nitrate.TestPlans.TreeView.updateChildPlan(treeview, planPK, 0, 'None');
    });
  }
};

Nitrate.TestPlans.SearchCase.on_load = function() {
    $('#id_product').change(update_category_select_from_product);
    if (!$('#id_category').val().length) {
        update_category_select_from_product();
    }

//fixme: for some reason when we clear Product categories are cleared
// but components are not. as if the on-change event doesn't execute!
// if we change to another Product both components and categories are
// updated
    $('#id_product').change(update_component_select_from_product);
    if (!$('#id_component').val().length) {
        update_component_select_from_product();
    }

  // new feature for searching by case id.
  var quick_search = jQ("#tp_quick_search_cases_form");
  var normal_search = jQ("#tp_normal_search_case_form");
  var quick_tab = jQ("#quick_tab");
  var normal_tab = jQ("#normal_tab");
  var search_mode = jQ("#search_mode");
  var errors = jQ(".errors");
  var triggerFormDisplay = function(options) {
    options.show.show();
    options.show_tab.addClass("profile_tab_active");
    options.hide.hide();
    options.hide_tab.removeClass("profile_tab_active");
  };

  jQ("#quick_search_cases").bind("click", function() {
    // clear errors
    errors.empty();
    search_mode.val("quick");
    triggerFormDisplay({
      "show": quick_search,
      "show_tab": quick_tab,
      "hide": normal_search,
      "hide_tab": normal_tab
    });
  });
  jQ("#normal_search_cases").bind("click", function() {
    // clear errors
    errors.empty();
    search_mode.val("normal");
    triggerFormDisplay({
      "show": normal_search,
      "show_tab": normal_tab,
      "hide": quick_search,
      "hide_tab": quick_tab
    });
  });

  if ($('#id_table_cases').length) {
    $('#id_table_cases').DataTable({
      "aoColumnDefs":[{ "bSortable":false, "aTargets":[ 'nosort' ] }],
      "aaSorting": [[ 1, "desc" ]],
      "sPaginationType": "full_numbers",
      "bFilter": false,
      "aLengthMenu": [[10, 20, 50, -1], [10, 20, 50, "All"]],
      "iDisplayLength": 20,
      "bProcessing": true
    });
  }

  if (jQ("#id_checkbox_all_cases").length) {
    bindSelectAllCheckbox(jQ('#id_checkbox_all_cases')[0], jQ('#id_form_cases')[0], 'case');
  }
};


function unlinkCasesFromPlan(plan_id, table) {
  const selection = serializeCaseFromInputList2(table);

  if (selection.empty()) {
    window.alert('At least one case is required to delete.');
    return false;
  }

  if (! confirm("Are you sure you want to delete test case(s) from this test plan?")) {
    return false;
  }

  selection.selectedCasesIds.forEach(function(case_id) {
    jsonRPC('TestPlan.remove_case', [plan_id, case_id], function(data){
        $(table).find(`tr[id="${case_id}"]`).hide();
    });
  });
}

function toggleTestCasePane(options, callback) {
  var case_id = options.case_id;
  var casePaneContainer = options.casePaneContainer;
  // defined if trying to expand a TestCase that is in review mode
  // otherwise not set
  var review_mode_param = '';
  if (options.review_mode) {
    review_mode_param = '?review_mode=1';
  }

  // If any of these is invalid, just keep quiet and don't display anything.
  if (case_id === undefined || casePaneContainer === undefined) {
    return;
  }

  casePaneContainer.toggle();

  if (casePaneContainer.find('.ajax_loading').length) {
    jQ.get('/case/' + case_id + '/readonly-pane/' + review_mode_param, function(data) {
      casePaneContainer.html(data);
      if (callback) {
        callback();
      }
    }, 'html');
  }

}


/*
 * Bind events on loaded cases.
 *
 * This is a closure. The real function needs cases container, plan's ID, and
 * initial parameters as the initializatio parameters.
 *
 * Arguments:
 * - container: the HTML element containing all loaded cases. Currently, the
 *   container is a TABLE.
 */
function bindEventsOnLoadedCases(options) {
  var parameters = options.parameters;
  var plan_id = options.plan_id;
  var cases_container = options.cases_container;

  return function(container, form) {
    jQ(cases_container)
      .find('.js-cases-list').find('input[name="case"]')
      .live('click', function(e) {
        Nitrate.TestPlans.Details.refreshCasesSelectionCheck(jQ(cases_container));
      });

    jQ(container).parent().find('.change_status_selector.js-just-loaded').bind('change', function(e) {
      var case_id = jQ(this).parent().parent()[0].id;
      changeTestCaseStatus(plan_id, [case_id], this.value, jQ(this).parents('.tab_list'));
    });

    // Display/Hide the case content
    jQ(container).parent().find('.expandable.js-just-loaded').bind('click', function(e) {
      var btn = this;
      var title = jQ(this).parent()[0]; // Container
      var content = jQ(this).parent().next()[0]; // Content Containers
      var case_id = title.id;
      var template_type = jQ(form).parent().find('input[name="template_type"]')[0].value;

      if (template_type === 'case') {
        toggleTestCasePane({ 'case_id': case_id, 'casePaneContainer': jQ(content) });
      } else if (template_type === 'review_case') {
          var review_case_content_callback = function(e) {
            var comment_container_t = jQ('<div>')[0];
            // Change status/comment callback
            var cc_callback = function(e) {
              e.stopPropagation();
              e.preventDefault();
              var params = Nitrate.Utils.formSerialize(this);
              var refresh_case = function(t) {
                var td = jQ('<td>', {colspan: 12});
                var id = 'id_loading_' + case_id;
                td.append(getAjaxLoading(id));
                jQ(content).html(td);
                fireEvent(btn, 'click');
                fireEvent(btn, 'click');
              }

                const comment_text = $(this).find('textarea[name=comment]').val();
                jsonRPC('TestCase.add_comment', [case_id, comment_text], function(data){
                    updateCommentsCount(case_id, true);
                    refresh_case();
                });
            };
            $(content).parent().find('.update_form').unbind('submit').bind('submit', cc_callback);

            // Observe the delete comment form
            var rc_callback = function(e) {
              e.stopPropagation();
              e.preventDefault();
              if (!window.confirm(default_messages.confirm.remove_comment)) {
                return false;
              }

                const comment_id = $(this).find('input[name=comment_id]').val();
                const comment_widget = $(this).parents().find("#comment"+comment_id);
                jsonRPC('TestCase.remove_comment', [case_id, comment_id], function(data){
                    $(comment_widget).hide();
                });
            };
            jQ(content).parent().find('.form_comment').unbind('submit');
            jQ(content).parent().find('.form_comment').bind('submit', rc_callback);
          };

          toggleTestCasePane({
            'case_id': case_id,
            'casePaneContainer': jQ(content),
            'review_mode': 1
          }, review_case_content_callback);
      } // end of review_case block

      toggleExpandArrow({ 'caseRowContainer': jQ(title), 'expandPaneContainer': jQ(content) });
    });

    /*
     * Using class just-loaded to identify thoes cases that are just loaded to
     * avoid register event handler repeatedly.
     */
    jQ(container).parent().find('.js-just-loaded').removeClass('js-just-loaded');
  };
}


/*
 * Serialize form data including the selected cases for AJAX requst.
 *
 * Used in function `constructPlanDetailsCasesZone'.
 */
function serializeFormData(options) {
  var form = options.form;
  var container = options.zoneContainer;
  var selection = options.casesSelection;
  var hashable = options.hashable || false;

  var formdata;
  if (hashable) {
    formdata = Nitrate.Utils.formSerialize(form);
  } else {
    formdata = jQ(form).serialize();
  }

  // some dirty data remains in the previous criteria, remove them.
  // FIXME: however, this is not a good way. CONSIDER to reuse filter form.
  var prevCriterias = jQ(container).find('.js-load-more')
    .attr('data-criterias')
    .replace(/a=\w+/, '')
    .replace(/&?selectAll=1/, '')
    .replace(/&?case=\d+/g, '');
  var unhashableData = prevCriterias;
  if (selection.selectAll) {
    unhashableData += '&selectAll=1';
  }
  var casepks = [''];
  var loopCount = selection.selectedCasesIds.length;
  var selectedCasesIds = selection.selectedCasesIds;
  for (var i = 0; i < loopCount; i++) {
    casepks.push('case=' + selectedCasesIds[i]);
  }
  unhashableData += casepks.join('&');

  if (hashable) {
    var arr = unhashableData.split('&');
    for (var i = 0; i < arr.length; i++) {
      var parts = arr[i].split('=');
      var key = parts[0], value = parts[1];
      // FIXME: not sure how key can be an empty string
      if (!key.length) {
        continue;
      }
      if (key in formdata) {
        // Before setting value, the original value must be converted to an array object.
        if (formdata[key].push === undefined) {
          formdata[key] = [formdata[key], value];
        } else {
          formdata[key].push(value);
        }
      } else {
        formdata[key] = value;
      }
    }
  } else {
    formdata += '&' + unhashableData;
  }

  return formdata;
}


function selectedCaseIds(container) {
    // return a list of case ids for currently selected test cases
    // in the UI
    var case_ids = [];
    jQ(container).find('.case_selector').each(function(index, element) {
        if (element.checked) {
            case_ids.push(element.value);
        }
    });
    return case_ids;
}


function changeTestCasePriority(plan_id, case_ids, new_value, container) {
    case_ids.forEach(function(element){
        jsonRPC('TestCase.update', [element, {priority: new_value}], function(data) {});
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
    constructPlanDetailsCasesZone(container, plan_id, parameters);
}

/*
 * To change selected cases' Reviewer or Default tester.
 */
function changeTestCaseActor(plan_id, case_ids, container, what_to_update) {
    var email_or_username = window.prompt('Please type new email or username');
    if (!email_or_username) {
      return false;
    }

    var cbAfterReviewerChanged = function(response) {
      var returnobj = jQ.parseJSON(response.responseText);
      if (returnobj.rc !== 0) {
        window.alert(returnobj.response);
        return false;
      }

      var template_type = 'case';

      if (what_to_update === 'reviewer') {
          template_type = 'review_case';
      }

      var parameters = {
          'a': 'initial',
          'from_plan': plan_id,
          'template_type': template_type,
      };

      constructPlanDetailsCasesZone(container, plan_id, parameters);
    };

    jQ.ajax({
      'type': 'POST',
      'url': '/ajax/update/cases-actor/',
      'data': {'username': email_or_username, 'case': case_ids, 'what_to_update': what_to_update},
      'success': function (data, textStatus, jqXHR) {
        cbAfterReviewerChanged(jqXHR);
      },
      'error': function (jqXHR, textStatus, errorThrown) {
        json_failure(jqXHR);
      }
    });
}

/*
 * Callback for constructPlanDetailsCasesZone.
 */
function constructPlanDetailsCasesZoneCallback(options) {
  var container = options.container;
  var plan_id = options.planId;
  var parameters = options.parameters;

  return function(response) {
    var form = jQ(container).children()[0];
    var table = jQ(container).children()[2];

    // Presume the first form element is the form
    if (form.tagName !== 'FORM') {
      window.alert('form element of container is not a form');
      return false;
    }

    var filter = jQ(form).parent().find('.list_filter')[0];

    // Filter cases
    jQ(form).bind('submit', function(e) {
      e.stopPropagation();
      e.preventDefault();
      var params = serialzeCaseForm(form, table, true, true);
      constructPlanDetailsCasesZone(container, plan_id, params);
    });

    // Change the case backgroud after selected
    jQ(form).parent().find('input[name="case"]').bind('click', function(e) {
      if (this.checked) {
        jQ(this).parent().parent().addClass('selection_row');
      } else {
        jQ(this).parent().parent().removeClass('selection_row');
      }
    });

    // Observe the check all selectbox
    if (jQ(form).parent().find('input[value="all"]').length) {
      var element = jQ(form).parent().find('input[value="all"]')[0];

      jQ(element).bind('click', function(e) {
        clickedSelectAll(this, jQ(this).closest('.tab_list')[0], 'case');
      });
    }

    if (jQ(form).parent().find('.btn_filter').length) {
      var element = jQ(form).parent().find('.btn_filter')[0];
      jQ(element).bind('click', function(t) {
        if (filter.style.display === 'none') {
          jQ(filter).show();
          jQ(this).html(default_messages.link.hide_filter);
        } else {
          jQ(filter).hide();
          jQ(this).html(default_messages.link.show_filter);
        }
      });
    }

    // Bind click the tags in tags list to tags field in filter
    if (jQ(form).parent().find('.taglist a[href="#testcases"]').length) {
      var elements = jQ(form).parent().find('.taglist a');
      elements.bind('click', function(e) {
        if (filter.style.display === 'none') {
          fireEvent(jQ(form).parent().find('.filtercase')[0], 'click');
        }
        form.tag__name__in.value = form.tag__name__in.value ? (form.tag__name__in.value
          + ',' + this.textContent) : this.textContent;

        // after clicking one of the tag values submit the form to refresh the list
        // of test cases. See https://github.com/kiwitcms/Kiwi/issues/426
        jQ(form).trigger('submit');
      });
    }

    // Bind the sort link
    if (jQ(form).parent().find('.btn_sort').length) {
      var element = jQ(form).parent().find('.btn_sort')[0];
      jQ(element).bind('click', function(e) {
        var params = serialzeCaseForm(form, table);
        var callback = function(t) {
          var returnobj = jQ.parseJSON(t.responseText);
          if (returnobj.rc != 0) {
            window.alert(returnobj.reponse);
          }
          params.a = 'initial';
          constructPlanDetailsCasesZone(container, plan_id, params);
        };
        resortCasesDragAndDrop(container, this, form, table, params, callback);
      });
    }

    jQ(container).find('input[value="all"]').live('click', function(e) {
        Nitrate.TestPlans.Details.toggleSelectAllInput(jQ(container));
    });

    var _bindEventsOnLoadedCases = bindEventsOnLoadedCases({
      'cases_container': container,
      'plan_id': plan_id,
      'parameters': parameters
    });
    _bindEventsOnLoadedCases(table, form);

    // Register event handler for loading more cases.
    Nitrate.TestPlans.Details.observeLoadMore(container.id);
    Nitrate.TestPlans.Details.showRemainingCasesCount(container.id);
    Nitrate.TestPlans.Details.refreshCasesSelectionCheck(jQ(container));
  };
}


function constructPlanDetailsCasesZone(container, plan_id, parameters) {
  if (typeof container === 'string') {
    container = jQ('#' + container)[0];
  }

  jQ(container).html('<div class="ajax_loading"></div>');

  var postData = parameters;
  if (!postData) {
    postData = {'a': 'initial', 'from_plan': plan_id};
  }

  var complete = constructPlanDetailsCasesZoneCallback({
    'container': container,
    'planId': plan_id,
    'parameters': postData
  });

  var url = Nitrate.http.URLConf.reverse({ name: 'search_case' });
  jQ.ajax({
    'url': url,
    'type': 'POST',
    'data': postData,
    'traditional': true,
    'success': function (data, textStatus, jqXHR) {
      jQ(container).html(data);

      var casesTable = jQ(container).find('.js-cases-list')[0];
      var navForm = jQ('#js-cases-nav-form')[0];

      jQ('#js-case-menu, #js-new-case').bind('click', function() {
        var params = jQ(this).data('params');
        window.location.href = params[0] + '?from_plan=' + params[1];
      });
      jQ('#js-add-case-to-plan').bind('click', function() {
        window.location.href = jQ(this).data('param');
      });
      jQ('#js-print-case').bind('click', function() {
        printableCases(jQ(this).data('param'), navForm, casesTable);
      });
      jQ('#js-clone-case').bind('click', function() {
        requestOperationUponFilteredCases({
          'url': jQ(this).data('param'),
          'form': navForm,
          'table': casesTable,
          'requestMethod': 'get'
        });
      });
      jQ('#js-remove-case').bind('click', function() {
        unlinkCasesFromPlan(plan_id, casesTable);
      });
      jQ('#js-new-run').bind('click', function() {
        requestOperationUponFilteredCases({
          'url': jQ(this).data('param'),
          'form': navForm,
          'table': casesTable,
          'requestMethod': 'post'
        });
      });

      jQ('.js-status-item').bind('click', function() {
        var new_value = jQ(this).data('param');
        var case_ids = selectedCaseIds(container);
        changeTestCaseStatus(plan_id, case_ids, new_value, jQ(container));
      });

      jQ('.js-priority-item').bind('click', function() {
        var new_value = jQ(this).data('param');
        var case_ids = selectedCaseIds(container);
        changeTestCasePriority(plan_id, case_ids, new_value, jQ(container));
      });

      jQ('input.btn_reviewer').bind('click', function() {
        var case_ids = selectedCaseIds(container);
        changeTestCaseActor(plan_id, case_ids, jQ(container), 'reviewer');
      });

      jQ('input.btn_default_tester').bind('click', function() {
        var case_ids = selectedCaseIds(container);
        changeTestCaseActor(plan_id, case_ids, jQ(container), 'default_tester');
      });

      jQ('#id_blind_all_link').find('.collapse-all').bind('click', function() {
        toggleAllCases(this);
      });
      jQ(casesTable).find('.js-case-field').bind('click', function() {
// todo: we don't need a POST and resort. This can be done with DataTables
// and we can leave sorting to the widget
        sortCase(container, jQ(this).parents('thead').data('param'), jQ(this).data('param'));
      });
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    },
    'complete': function() {
      complete();
    }
  });
}


function sortCase(container, plan_id, order) {
  var form = jQ(container).children()[0];
  var parameters = Nitrate.Utils.formSerialize(form);
  parameters.a = 'sort';

  if (parameters.case_sort_by == order) {
    parameters.case_sort_by = '-' + order;
  } else {
    parameters.case_sort_by = order;
  }
  constructPlanDetailsCasesZone(container, plan_id, parameters);
}


function resortCasesDragAndDrop(container, button, form, table, parameters, callback) {
  if (button.innerHTML !== 'Done Sorting') {
    // Remove the elements affact the page
    jQ(form).parent().find('.blind_all_link').remove(); // Remove blind all link
    jQ(form).parent().find('.case_content').remove();
    jQ(form).parent().find('.blind_icon').remove();
    jQ(form).parent().find('.show_change_status_link').remove();
    jQ(table).parent().find('.expandable').unbind();

    // Use the selector content to replace the selector
    jQ(form).parent().find('.change_status_selector').each(function(t) {
      var w = this.selectedIndex;
      jQ(this).replaceWith((jQ('<span>')).html(this.options[w].text));
    });

    // init the tableDnD object
    new TableDnD().init(table);
    button.innerHTML = 'Done Sorting';
    jQ(table).parent().find('tr').addClass('cursor_move');
  } else {
    jQ(button).replaceWith((jQ('<span>')).html('...Submitting changes'));

    jQ(table).parent().find('input[type=checkbox]').each(function(t) {
      this.checked = true;
      this.disabled = false;
    });

    var url = 'reorder-cases/';

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
}


/*
 * Request specific operation upon filtered TestCases.
 *
 * Default HTTP method is GET.
 *
 * Options:
 * - url: the URL representing the service requesting to now.
 * - form: containing all necessary data serialized as the data included in REQUEST.
 * - casesContainer: containing all INPUT with type checkbox, each of them holds every filtered
 *                   TestCase' Id. Typcicall, it's a TABLE in the current implementation.
 *
 * FIXME: this function is similar to some other functions within tcms_actions.js, that wraps
 *        function postToURL. All these functions have almost same behavior. Abstraction can be done
 *        better.
 */
function requestOperationUponFilteredCases(options) {
  var requestMethod = options.requestMethod || 'get';
  var url = options.url;
  var form = options.form;
  var casesContainer = options.table;

  var selection = serializeCaseFromInputList2(casesContainer);
  if (selection.empty()) {
    window.alert('At least one case is required by a run.');
    return false;
  }
  // Exclude selected cases, that will be added from the selection.
  var params = serialzeCaseForm(form, casesContainer, true, true);
  if (selection.selectAll) {
    params.selectAll = selection.selectAll;
  }
  params.case = selection.selectedCasesIds;
  postToURL(url, params, requestMethod);
}
