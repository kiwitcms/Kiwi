var expandedTestCaseIds = [],
    fadeAnimationTime = 500;

const allTestCases = {};

$(document).ready(function() {
    const testPlanId = $('#test_plan_pk').data('testplanPk');

    const permissions = {
        'perm-change-testcase': $('#test_plan_pk').data('perm-change-testcase') === 'True',
        'perm-remove-testcase': $('#test_plan_pk').data('perm-remove-testcase') === 'True',
        'perm-add-testcase': $('#test_plan_pk').data('perm-add-testcase') === 'True'
    };

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
    });

    toolbarDropdowns();
    toolbarEvents();
});

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

function getTestCaseRowContent(rowContent, testCase, permissions) {
    var row = $(rowContent);

    row[0].firstElementChild.dataset.testcasePk = testCase.id;
    row.find('.js-test-case-link').html(`TC-${testCase.id}: ${testCase.summary}`).attr('href', `/case/${testCase.id}/`);
    row.find('.js-test-case-priority').html(`${testCase.priority}`);
    row.find('.js-test-case-category').html(`${testCase.category}`);
    row.find('.js-test-case-author').html(`${testCase.author}`);
    row.find('.js-test-case-tester').html(`${testCase.default_tester || '-'}`);

    // set the links in the kebab menu
    if (permissions['perm-change-testcase']) {
        row.find('.js-test-case-menu-edit')[0].href = `/case/${testCase.id}/edit/`;
    }

    if (permissions['perm-add-testcase']) {
        row.find('.js-test-case-menu-clone')[0].href = `/cases/clone/?case=${testCase.id}`;
    }

    // apply visual separation between confirmed and not confirmed

    if (!isTestCaseConfrimed(testCase.case_status_id)) {
        row.find('.list-group-item-header').addClass('bg-danger');
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
    // todo use markdown converter to show tc.text as html
    row.find('.js-test-case-expand-text').html(testCase.text);
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
            var email_or_username = window.prompt($('#test_plan_pk').data('trans-default-tester-prompt-message'));
            if (!email_or_username) {
                return;
            }
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'default_tester': email_or_username}], function(tc) {
                const testCaseRow = $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`);
                testCaseRow.fadeOut(fadeAnimationTime, function() {
                    testCaseRow.find('.js-test-case-tester').html(tc.default_tester);
                }).fadeIn(fadeAnimationTime);
            });
        });


        $('.js-test-case-menu-priority').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'priority': ev.target.dataset.id}], function() {
                const testCaseRow = $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`);
                testCaseRow.fadeOut(fadeAnimationTime, function() {
                    testCaseRow.find('.js-test-case-priority').html(ev.target.innerText);
                }).fadeIn(fadeAnimationTime);
            });
        });

        $('.js-test-case-menu-status').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'case_status': ev.target.dataset.id}], function() {
                if (isTestCaseConfrimed(ev.target.dataset.id)) {
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

function toolbarEvents() {

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
}

function toolbarDropdowns() {
    let toolbarDropdown= $('#toolbar-dropdown')[0].content;

    $('.js-toolbar-filter-options').append(toolbarDropdown.cloneNode(true));
    $('.js-toolbar-sort-options').append(toolbarDropdown.cloneNode(true));
}

function isTestCaseConfrimed(status) {
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

        let value1 = allTestCases[tc1Id][sortBy] || "",
            value2 = allTestCases[tc2Id][sortBy] || "";

        return value1.localeCompare(value2) * sortOrder;
    });

    //put the new order in the DOM
    tcsParentElement.html(visibleTCrows);
}
