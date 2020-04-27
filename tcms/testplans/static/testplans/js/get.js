$(document).ready(function() {
    const testPlanId = $('#test_plan_pk').data('testplanPk');
    const testCases = {
        'confirmed': {},
        'not_confirmed': {}
    };

    const permissions = {
        'perm-change-testcase': $('#test_plan_pk').data('perm-change-testcase') === 'True',
        'perm-remove-testcase': $('#test_plan_pk').data('perm-remove-testcase') === 'True'
    };

    // bind everything in tags table
    const perm_remove_tag = $('#test_plan_pk').data('perm-remove-tag') === 'True';
    tagsCard('TestPlan', testPlanId, {plan: testPlanId}, perm_remove_tag);

    jsonRPC('TestCase.filter', [{'plan': testPlanId}], function(data) {
        for (var i = 0; i < data.length; i++) {
            var testCase = data[i];
            //todo: refactor when testcase_status is replaced with boolean flag
            if (testCase.case_status_id === 2) {
                testCases.confirmed[testCase.id] = testCase;
            } else {
                testCases.not_confirmed[testCase.id] = testCase;
            }
        }
        drawTestCases(testCases.confirmed, testPlanId, permissions);
        treeViewBind();
    });

});

function drawTestCases(testCases, testPlanId, permissions) {
    var container = $('#confirmed-testcases'),
        noCasesTemplate = $('#no_test_cases'),
        testCaseRowDocumentFragment = $('#test_case_row')[0].content;

    if (Object.keys(testCases).length > 0) {
       for (const testCaseId in testCases) {
            container.append(getTestCaseRowContent(testCaseRowDocumentFragment.cloneNode(true), testCases[testCaseId], permissions));
        }
        attachEvents(testPlanId, permissions);
        if (permissions['perm-change-testcase']) {
            drawStatusAndPriority();
        }
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

    // set the link in the kebab menu
    if (permissions['perm-change-testcase']) {
        row.find('.js-test-case-menu-edit')[0].href = `/case/${testCase.id}/edit/`;
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

    getTestCaseExpandArea(row, testCase);

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

function attachEvents(testPlanId, permissions) {
    if (permissions['perm-change-testcase']) {
        // update default tester
        $('.js-test-case-menu-tester').click(function(ev) {
            var email_or_username = window.prompt($('#test_plan_pk').data('trans-default-tester-prompt-message'));
            if (!email_or_username) {
                return;
            }
            const testCaseId = getCaseIdFromEvent(ev);

            // default_tester can be update only if we pass an user id
            jsonRPC('TestCase.update', [testCaseId, {'default_tester': email_or_username}], function(res) {
                // todo update tc row data
            });
        });


        $('.js-test-case-menu-priority').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'priority': ev.target.dataset.id}], function(result) {
                // todo update tc row data
            });
        });

        $('.js-test-case-menu-status').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestCase.update', [testCaseId, {'case_status': ev.target.dataset.id}], function(result) {
                // todo update tc row data
            });
        });
    }

    if (permissions['perm-remove-testcase']) {
        // delete testcase from the plan
        $('.js-test-case-menu-delete').click(function(ev) {
            const testCaseId = getCaseIdFromEvent(ev);
            jsonRPC('TestPlan.remove_case', [testPlanId, testCaseId], function(res) {
                $("div").find(`[data-testcase-pk=${testCaseId}]`).remove();
            });
        });
    }

    function getCaseIdFromEvent(ev) {
        return $(ev.target).closest('.list-group-item').data('testcase-pk');
    }
}

function drawStatusAndPriority() {

    jsonRPC('TestCaseStatus.filter', {}, function(statuses) {
        const listItemTemplateFragment = $('#menu-status-item')[0].content;

        var listItemsNodes = [];

        for (var i = 0; i < statuses.length; i++) {
            var liElement = $(listItemTemplateFragment.cloneNode(true)),
                testCaseStatus = statuses[i];

            liElement.find('a').text(testCaseStatus.name);
            liElement.find('a')[0].dataset.id = testCaseStatus.id;
            listItemsNodes.push(liElement);
        }

        $('.js-test-case-menu-status').each(function() {
            for (var i = 0; i < listItemsNodes.length; i++) {
                // clone must be used, because items will be added only to the first TC
                $(this).append(listItemsNodes[i].clone());
            }
        });
    });

    jsonRPC('Priority.filter', {}, function(priorities) {
        const listItemTemplateFragment = $('#menu-priority-item')[0].content;

        var listItemsNodes = [];

        for (var i = 0; i < priorities.length; i++) {
            var liElement = $(listItemTemplateFragment.cloneNode(true)),
                priority = priorities[i];

            liElement.find('a').text(priority.value);
            liElement.find('a')[0].dataset.id = priority.id;
            listItemsNodes.push(liElement);
        }

        $('.js-test-case-menu-priority').each(function() {
            for (var i = 0; i < listItemsNodes.length; i++) {
                // clone must be used, because items will be added only to the first TC
                $(this).append(listItemsNodes[i].clone());
            }
        });
    });
}
