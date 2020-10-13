var expandedTestCaseIds = [],
    fadeAnimationTime = 500;

const allTestCases = {},
      autocomplete_cache = {};


$(document).ready(function() {
    const testPlanId = $('#test_plan_pk').data('testplanPk');

    const permissions = {
        'perm-change-testcase': $('#test_plan_pk').data('perm-change-testcase') === 'True',
        'perm-remove-testcase': $('#test_plan_pk').data('perm-remove-testcase') === 'True',
        'perm-add-testcase': $('#test_plan_pk').data('perm-add-testcase') === 'True'
    };

    $('#btn-search-cases').click(function () {
        return searchAndSelectTestCases(testPlanId, $(this).attr('href'));
    });

    // bind everything in tags table
    const perm_remove_tag = $('#test_plan_pk').data('perm-remove-tag') === 'True';
    tagsCard('TestPlan', testPlanId, {plan: testPlanId}, perm_remove_tag);

    jsonRPC('TestCase.filter', [{'plan': testPlanId}], function(data) {
        for (var i = 0; i < data.length; i++) {
            var testCase = data[i];
            allTestCases[testCase.id] = testCase;
        }
        drawTestCases(allTestCases, testPlanId, permissions);
        treeViewBind();

        // b/c treeViewBind() will modify handlers/visibility for both
        // test plan family tree and the test cases tree
        adjustTestPlanFamilyTree();

        // b/c drag & reorder needs the initial order of test cases and
        // they may not be fully loaded when sortable() is initialized!
        toolbarEvents(testPlanId, permissions);
    });

    collapseDocumentText();
    initTestCaseSearchAndAdd(testPlanId);
});


function searchAndSelectTestCases(planId, href) {
    $('#popup-selection').val('');
    popupWindow = showPopup(`${href}?allow_select=1`);

    $(popupWindow).on('beforeunload', function(){
        const testCaseIDs = $('#popup-selection').val();

        if (testCaseIDs) {
            // add the selected test cases
            testCaseIDs.split(",").forEach(function(testCase) {
                jsonRPC('TestPlan.add_case', [planId, testCase], function(result) {}, true)
            })

            window.location.reload(true);
            // TODO: remove the page reload above and add the new case to the list
        }
    });

    return false;
}

function showPopup(href) {
    if (href.indexOf('?') === -1) {
        href += '?nonav=1';
    } else {
        href += '&nonav=1';
    }

    const win = window.open(href, 'popup page', 'width=1024,height=612');
    win.focus();

    return win;
}

function addTestCaseToPlan(planId) {
    const caseName = $('#search-testcase')[0].value;
    const testCase = autocomplete_cache[caseName];

    // test case is already present so don't add it
    if (allTestCases[testCase.id]) {
        $('#search-testcase').val('');
        return false;
    }

    jsonRPC('TestPlan.add_case', [planId, testCase.id], function(result) {
        // IMPORTANT: the API result includes a 'sortkey' field value!
        window.location.reload(true);

        // TODO: remove the page reload above and add the new case to the list
        // NB: pay attention to drawTestCases() & treeViewBind()
        // NB: also add to allTestCases !!!

        $('#search-testcase').val('');
    });
}


function initTestCaseSearchAndAdd(planId) {
    // + button
    $('#btn-add-case').click(function() {
        addTestCaseToPlan(planId);

        return false;
    });

    // Enter key
    $('#search-testcase').keyup(function(event) {
        if (event.keyCode === 13) {
            addTestCaseToPlan(planId);

            return false;
        };
    });

    // autocomplete
    $('#search-testcase.typeahead').typeahead({
        minLength: 1,
        highlight: true
        }, {
        name: 'testcases-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function(element) {
            const displayName = `TC-${element.id}: ${element.summary}`;
            autocomplete_cache[displayName] = element;
            return displayName;
        },
        source: function(query, processSync, processAsync) {
            // accepts "TC-1234" or "tc-1234" or "1234"
            query = query.toLowerCase().replace('tc-', '');
            if (query === '') {
                return;
            }

            var rpc_query = {pk: query};

            // or arbitrary string
            if (isNaN(query)) {
                if (query.length >=3) {
                    rpc_query = {summary__icontains: query};
                } else {
                    return;
                }
            }

            jsonRPC('TestCase.filter', rpc_query, function(data) {
                return processAsync(data);
            });
        }
    });
}



function collapseDocumentText() {
    // for some reason .height() reports a much higher value than
    // reality and the 59% reduction seems to work nicely
    const infoCardHeight = 0.59 * $('#testplan-info').height();

    if ($('#testplan-text').height() > infoCardHeight) {
        $('#testplan-text-collapse-btn').removeClass('hidden');

        $('#testplan-text').css('min-height', infoCardHeight);
        $('#testplan-text').css('height', infoCardHeight);
        $('#testplan-text').css('overflow', 'hidden');

        $('#testplan-text').on('hidden.bs.collapse', function () {
            $('#testplan-text').removeClass('collapse').css({
                'height': infoCardHeight
            })
        });
    }
}

function adjustTestPlanFamilyTree() {
    // remove the > arrows from elements which don't have children
    $('#test-plan-family-tree').find(".list-group-item-container").each(function(index, element){
        if (!element.innerHTML.trim()) {
            const span = $(element).siblings('.list-group-item-header').find('.list-view-pf-left span');

            span.removeClass('fa-angle-right');
            // this is the exact same width so rows are still aligned
            span.attr('style', 'width:9px');
        }
    });

    // expand all parent elements so that the current one is visible
    $('#test-plan-family-tree').find(".list-group-item.active").each(function(index, element){
        $(element).parents('.list-group-item-container').each(function(idx, container){
            $(container).toggleClass('hidden');
        });
    });
}

function drawTestCases(testCases, testPlanId, permissions) {
    var container = $('#testcases-list'),
        noCasesTemplate = $('#no_test_cases'),
        testCaseRowDocumentFragment = $('#test_case_row')[0].content;

    if (Object.keys(testCases).length > 0) {
        for (const testCaseId in testCases) {
            container.append(getTestCaseRowContent(testCaseRowDocumentFragment.cloneNode(true), testCases[testCaseId], permissions));
        }
        attachEvents(testCases, testPlanId, permissions);
    } else {
        container.append(noCasesTemplate[0].innerHTML);
    }
}

function redrawSingleRow(testCaseId, testPlanId, permissions) {
    var testCaseRowDocumentFragment = $('#test_case_row')[0].content,
        newRow = getTestCaseRowContent(testCaseRowDocumentFragment.cloneNode(true), allTestCases[testCaseId], permissions);

    // replace the element in the dom
    $(`[data-testcase-pk=${testCaseId}]`).replaceWith(newRow);
    attachEvents(allTestCases[testCaseId], testPlanId, permissions);
}

function getTestCaseRowContent(rowContent, testCase, permissions) {
    var row = $(rowContent);

    row[0].firstElementChild.dataset.testcasePk = testCase.id;
    row.find('.js-test-case-link').html(`TC-${testCase.id}: ${testCase.summary}`).attr('href', `/case/${testCase.id}/`);
    // todo: TestCaseStatus here isn't translated b/c TestCase.filter uses a
    // custom serializer which needs to be refactored as well
    row.find('.js-test-case-status').html(`${testCase.case_status}`);
    row.find('.js-test-case-priority').html(`${testCase.priority}`);
    row.find('.js-test-case-category').html(`${testCase.category}`);
    row.find('.js-test-case-author').html(`${testCase.author}`);
    row.find('.js-test-case-tester').html(`${testCase.default_tester || '-'}`);
    row.find('.js-test-case-reviewer').html(`${testCase.reviewer || '-'}`);

    // set the links in the kebab menu
    if (permissions['perm-change-testcase']) {
        row.find('.js-test-case-menu-edit')[0].href = `/case/${testCase.id}/edit/`;
    }

    if (permissions['perm-add-testcase']) {
        row.find('.js-test-case-menu-clone')[0].href = `/cases/clone/?case=${testCase.id}`;
    }

    // apply visual separation between confirmed and not confirmed

    if (!isTestCaseConfirmed(testCase.case_status_id)) {
        row.find('.list-group-item-header').addClass('bg-danger');

        // add customizable icon as part of #1932
        row.find('.js-test-case-status-icon').addClass('fa-times')

        row.find('.js-test-case-tester-div').toggleClass('hidden');
        row.find('.js-test-case-reviewer-div').toggleClass('hidden');
    } else {
        row.find('.js-test-case-status-icon').addClass('fa-check-square')
    }

    //handle automated icon
    var automation_indication_element = row.find('.js-test-case-automated'),
        automated_class_to_remove = 'fa-cog';

    if (testCase.is_automated) {
        automated_class_to_remove = 'fa-thumbs-up';
    }

    automation_indication_element.parent().attr(
        'title',
        automation_indication_element.data(testCase.is_automated.toString())
    );
    automation_indication_element.removeClass(automated_class_to_remove);

    return row;
}

function getTestCaseExpandArea(row, testCase) {
    markdown2HTML(testCase.text, row.find('.js-test-case-expand-text'))
    if (testCase.notes.trim().length > 0) {
        row.find('.js-test-case-expand-notes').html(testCase.notes);
    }

    // draw the attachments
    var uniqueDivCustomId = `js-tc-id-${testCase.id}-attachments`;
    // set unique identifier so we know where to draw fetched data
    row.find('.js-test-case-expand-attachments').parent()[0].id = uniqueDivCustomId;

    jsonRPC('TestCase.list_attachments', [testCase.id], function(data) {

        // cannot use instance of row in the callback
        var ulElement = $(`#${uniqueDivCustomId} .js-test-case-expand-attachments`);

        if (data.length === 0) {
            ulElement.children().removeClass('hidden');
            return;
        }

        var liElementFragment = $('#attachments-list-item')[0].content;

        for (var i = 0; i < data.length; i++) {
            //should create new element for every attachment
            var liElement = liElementFragment.cloneNode(true),
                attachmentLink = $(liElement).find('a')[0];

            attachmentLink.href = data[i].url;
            attachmentLink.innerText = data[i].url.split('/').slice(-1)[0];
            ulElement.append(liElement);
        }
    });
}

function attachEvents(testCases, testPlanId, permissions) {
    if (permissions['perm-change-testcase']) {
        // update default tester
        $('.js-test-case-menu-tester').click(function(ev) {
            var emailOrUsername = window.prompt($('#test_plan_pk').data('trans-default-tester-prompt-message'));
            if (!emailOrUsername) {
                return;
            }
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'default_tester': emailOrUsername}], function(tc) {
                const testCaseRow = $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`);
                animate(testCaseRow, function() {
                    testCaseRow.find('.js-test-case-tester').html(tc.default_tester);
                });
            });
        });


        $('.js-test-case-menu-priority').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'priority': ev.target.dataset.id}], function() {
                const testCaseRow = $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`);
                animate(testCaseRow, function() {
                    testCaseRow.find('.js-test-case-priority').html(ev.target.innerText);
                });
            });
        });

        $('.js-test-case-menu-status').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'case_status': ev.target.dataset.id}], function() {
                if (isTestCaseConfirmed(ev.target.dataset.id)) {
                    $(ev.target).closest('.list-group-item-header').removeClass('bg-danger');
                } else {
                    $(ev.target).closest('.list-group-item-header').addClass('bg-danger');
                }
            });
        });
    }

    if (permissions['perm-remove-testcase']) {
        // delete testcase from the plan
        $('.js-test-case-menu-delete').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);
            jsonRPC('TestPlan.remove_case', [testPlanId, testCaseId], function() {
                delete allTestCases[testCaseId];

                // fadeOut the row then remove it from the dom, if we remove it directly the user may not see the change
                $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`).fadeOut(fadeAnimationTime, function() {
                    $(this).remove();
                });
            });
        });
    }

    // get details and draw expand area only on expand
    $('.js-testcase-row').click(function(ev) {
        const testCaseId = getCaseIdFromEvent(ev);

        // tc was expanded once, dom is ready
        if (expandedTestCaseIds.indexOf(testCaseId) > -1) {
            return;
        }

        const tcRow = $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`);
        expandedTestCaseIds.push(testCaseId);
        getTestCaseExpandArea(tcRow, testCases[testCaseId]);
    });


    let inputs = $('.js-testcase-row').find('input');
    inputs.click(function(ev) {
        const checkbox = $('.js-checkbox-toolbar')[0];

        inputs.each(function(index, tc) {
            checkbox.checked = tc.checked;

            if (!checkbox.checked) {
                return false;
            }
        });
    });

    function getCaseIdFromEvent(ev) {
        return $(ev.target).closest('.js-testcase-row').data('testcase-pk');
    }
}

function toolbarEvents(testPlanId, permissions) {
    toolbarDropdowns();

    $('.js-checkbox-toolbar').click(function(ev) {
        const isChecked = ev.target.checked;
        const testCaseRows = $('.js-testcase-row').find('input');

        testCaseRows.each(function(index, tc) {
            tc.checked = isChecked;
        });
    });

    $('.js-toolbar-filter-options li').click(function(ev) {
        changeDropdownSelectedItem('.js-toolbar-filter-options', '#input-filter-button' , ev.target);
    });

    $('#toolbar-filter').on("keyup", function() {
        let filterValue = $(this).val().toLowerCase();
        let filterBy = $('.js-toolbar-filter-options .selected')[0].dataset.filterType;

        filterTestCasesByProperty(
            allTestCases,
            filterBy,
            filterValue
        );

    });

    $('.js-toolbar-sort-options li').click(function(ev) {
        changeDropdownSelectedItem('.js-toolbar-sort-options', '#sort-button', ev.target);

        sortTestCases();
    });

    //handle asc desc icon
    $('.js-toolbar-sorting-order > span').click(function(ev) {
        let icon = $(this);

        icon.siblings('.hidden').removeClass('hidden');
        icon.addClass('hidden');

        sortTestCases();
    });


    // always initialize the sortable list however you can only
    // move items using the handle icon on the left which becomes
    // visible only when the manual sorting button is clicked
    sortable('#testcases-list', {
        handle: '.handle',
        itemSerializer: (serializedItem, sortableContainer) => {
            return parseInt(serializedItem.node.getAttribute('data-testcase-pk'))
        }
    });

    // IMPORTANT: this is not empty b/c sortable() is initialized *after*
    // all of the test cases have been rendered !!!
    const initialOrder = sortable('#testcases-list', 'serialize')[0].items;

    $('.js-toolbar-manual-sort').click(function(event) {
        $(this).blur();
        $('.js-toolbar-manual-sort').find('span').toggleClass(['fa-sort', 'fa-check-square']);
        $('.js-testcase-sort-handler, .js-testcase-expand-arrow, .js-testcase-checkbox').toggleClass('hidden');

        const currentOrder = sortable('#testcases-list', 'serialize')[0].items;

        // rows have been rearranged and the results must be committed to the DB
        if (currentOrder.join() !== initialOrder.join()) {
            currentOrder.forEach(function(tc_pk, index) {
                jsonRPC('TestPlan.update_case_order', [testPlanId, tc_pk, index*10], function(result) {});
            });
        }
    });


    $('.js-toolbar-priority').click(function(ev) {
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return;
        }

        for (let i = 0; i < selectedCases.length; i++) {
            let testCaseId = selectedCases[i];
            jsonRPC('TestCase.update', [testCaseId, {'priority': ev.target.dataset.id}], function() {
                const testCaseRow = $(`.js-testcase-row[data-testcase-pk=${testCaseId}]`);
                animate(testCaseRow, function() {
                    testCaseRow.find('.js-test-case-priority').html(ev.target.innerText);
                });
            });
        }

    });

    $('.js-toolbar-status').click(function(ev) {
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return;
        }

        for (let i = 0; i < selectedCases.length; i++) {
            let testCaseId = selectedCases[i],
                newStatus = ev.target.dataset.id;

            jsonRPC('TestCase.update', [testCaseId, {'case_status': newStatus}], function() {
                const testCaseRow = $(`.js-testcase-row[data-testcase-pk=${testCaseId}]`);
                animate(testCaseRow, function() {
                    let tcRowHeader = $(this).find('.list-group-item-header');

                    if (isTestCaseConfirmed(newStatus)) {
                        tcRowHeader.removeClass('bg-danger');
                    } else {
                        tcRowHeader.addClass('bg-danger');
                    }

                });
            });
        }

    });

    $('#delete_button').click(function(ev) {
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return;
        }

        const areYouSureText = $('#test_plan_pk').data('trans-are-you-sure');
        if (confirm(areYouSureText)) {
            for (let i = 0; i < selectedCases.length; i++) {
                let testCaseId = selectedCases[i];
                jsonRPC('TestPlan.remove_case', [testPlanId, testCaseId], function() {
                    delete allTestCases[testCaseId];

                    // fadeOut the row then remove it from the dom, if we remove it directly the user may not see the change
                    $(`[data-testcase-pk=${testCaseId}]`).fadeOut(fadeAnimationTime, function() {
                        $(this).remove();
                    });
                });
            }
        }
    });

    $('#default-tester-button').click(function(ev) {
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return;
        }

        var emailOrUsername = window.prompt($('#test_plan_pk').data('trans-default-tester-prompt-message'));
        
        if (!emailOrUsername) {
            return;
        }

        for (let i = 0; i < selectedCases.length; i++) {
            let testCaseId = selectedCases[i];

            jsonRPC('TestCase.update', [testCaseId, {'default_tester': emailOrUsername}], function(tc) {
                const testCaseRow = $(`[data-testcase-pk=${testCaseId}]`);

                //update the data
                allTestCases[testCaseId].default_tester = tc.default_tester;

                animate(testCaseRow, function() {
                    redrawSingleRow(testCaseId, testPlanId, permissions);
                });
            });
        }

    });

    $('#bulk-clone-button').click(function() {
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return;
        }

         window.location.assign(`/cases/clone?case=${selectedCases.join('&case=')}`);
    });
}

function toolbarDropdowns() {
    let toolbarDropdown= $('#toolbar-dropdown')[0].content;

    $('.js-toolbar-filter-options').append(toolbarDropdown.cloneNode(true));
    $('.js-toolbar-sort-options').append(toolbarDropdown.cloneNode(true));
}

function isTestCaseConfirmed(status) {
    //todo: refactor when testcase_status is replaced with boolean flag
    return Number(status) === 2;
}

// on dropdown change update the label of the button and set new selected list item
function changeDropdownSelectedItem(dropDownSelector, buttonSelector, target) {
    $(`${buttonSelector}`)[0].innerHTML = target.innerText + '<span class="caret"></span>';

    //remove selected class
    $(`${dropDownSelector} li`).each(function(index, el) {
        el.className = '';
    });

    // target is a tag
    target.parentElement.className = 'selected';
}

function sortTestCases() {

    let sortBy = $('.js-toolbar-sort-options .selected')[0].dataset.filterType,
        tcsParentElement = $('#testcases-list'),
        visibleTCrows = $('.js-testcase-row:visible'),
        sortOrder = $('.js-toolbar-sorting-order > span:not(.hidden)').data('order');


    // reorder the tc rows
    visibleTCrows.sort(function(tc1, tc2) {
        let tc1Id = $(tc1).data('testcasePk'),
            tc2Id = $(tc2).data('testcasePk');

        let value1 = allTestCases[tc1Id][sortBy].toString() || "",
            value2 = allTestCases[tc2Id][sortBy].toString() || "";

        return value1.localeCompare(value2) * sortOrder;
    });

    //put the new order in the DOM
    tcsParentElement.html(visibleTCrows);
}


// todo check selectedCheckboxes function in testrun/get.js  
function getSelectedTestCases() {
    let inputs = $('.js-testcase-row input:checked'),
        tcIds = [];

    inputs.each(function(index, el) {
        let elJq = $(el);

        if (elJq.is(':hidden')) {
            return;
        }

        let id = elJq.closest('.js-testcase-row').data('testcase-pk');
        tcIds.push(id);
    });

    return tcIds;

}
