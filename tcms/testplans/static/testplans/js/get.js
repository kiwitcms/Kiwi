var expandedTestCaseIds = [],
    fadeAnimationTime = 500;

const allTestCases = {},
      autocomplete_cache = {};

let confirmedStatuses = [];


$(document).ready(function() {
    const testPlanDataElement = $('#test_plan_pk');
    const testPlanId = testPlanDataElement.data('testplan-pk');

    const permissions = {
        'perm-change-testcase': testPlanDataElement.data('perm-change-testcase') === 'True',
        'perm-remove-testcase': testPlanDataElement.data('perm-remove-testcase') === 'True',
        'perm-add-testcase': testPlanDataElement.data('perm-add-testcase') === 'True',
        'perm-add-comment': testPlanDataElement.data('perm-add-comment') === 'True',
        'perm-delete-comment': testPlanDataElement.data('perm-delete-comment') === 'True'
    };

    // bind everything in tags table
    const perm_remove_tag = testPlanDataElement.data('perm-remove-tag') === 'True';
    tagsCard('TestPlan', testPlanId, {plan: testPlanId}, perm_remove_tag);

    jsonRPC('TestCaseStatus.filter', {is_confirmed: true}, function(statuses) {
        // save for later use
        for (let i = 0; i < statuses.length; i++) {
            confirmedStatuses.push(statuses[i].id);
        }

        jsonRPC('TestCase.sortkeys', {'plan': testPlanId}, function(sortkeys) {
            jsonRPC('TestCase.filter', {'plan': testPlanId}, function(data) {
                for (var i = 0; i < data.length; i++) {
                    var testCase = data[i];

                    testCase.sortkey = sortkeys[testCase.id];
                    allTestCases[testCase.id] = testCase;
                }
                sortTestCases(Object.values(allTestCases), testPlanId, permissions, 'sortkey');

                // drag & reorder needs the initial order of test cases and
                // they may not be fully loaded when sortable() is initialized!
                toolbarEvents(testPlanId, permissions);
            });
        });
    });

    adjustTestPlanFamilyTree();
    collapseDocumentText();
    quickSearchAndAddTestCase(testPlanId, addTestCaseToPlan, autocomplete_cache);
    $('#btn-search-cases').click(function () {
        return advancedSearchAndAddTestCases(
            testPlanId, 'TestPlan.add_case', $(this).attr('href'),
            $('#test_plan_pk').data('trans-error-adding-cases')
        );
    });
});

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
    treeViewBind('#test-plan-family-tree');

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

    if (testCases.length > 0) {
        testCases.forEach(function(element) {
            container.append(getTestCaseRowContent(testCaseRowDocumentFragment.cloneNode(true), element, permissions));
        })
        attachEvents(testPlanId, permissions);
    } else {
        container.append(noCasesTemplate[0].innerHTML);
    }
}

function redrawSingleRow(testCaseId, testPlanId, permissions) {
    var testCaseRowDocumentFragment = $('#test_case_row')[0].content,
        newRow = getTestCaseRowContent(testCaseRowDocumentFragment.cloneNode(true), allTestCases[testCaseId], permissions);

    // remove from expanded list b/c the comment section may have changed
    delete expandedTestCaseIds[expandedTestCaseIds.indexOf(testCaseId)];

    // replace the element in the dom
    $(`[data-testcase-pk=${testCaseId}]`).replaceWith(newRow);
    attachEvents(testPlanId, permissions);
}

function getTestCaseRowContent(rowContent, testCase, permissions) {
    var row = $(rowContent);

    row[0].firstElementChild.dataset.testcasePk = testCase.id;
    row.find('.js-test-case-link').html(`TC-${testCase.id}: ${testCase.summary}`).attr('href', `/case/${testCase.id}/`);
    // todo: TestCaseStatus here isn't translated b/c TestCase.filter uses a
    // custom serializer which needs to be refactored as well
    row.find('.js-test-case-status').html(`${testCase.case_status__name}`);
    row.find('.js-test-case-priority').html(`${testCase.priority__value}`);
    row.find('.js-test-case-category').html(`${testCase.category__name}`);
    row.find('.js-test-case-author').html(`${testCase.author__username}`);
    row.find('.js-test-case-tester').html(`${testCase.default_tester__username || '-'}`);
    row.find('.js-test-case-reviewer').html(`${testCase.reviewer__username || '-'}`);

    // set the links in the kebab menu
    if (permissions['perm-change-testcase']) {
        row.find('.js-test-case-menu-edit')[0].href = `/case/${testCase.id}/edit/`;
    }

    if (permissions['perm-add-testcase']) {
        row.find('.js-test-case-menu-clone')[0].href = `/cases/clone/?case=${testCase.id}`;
    }

    // apply visual separation between confirmed and not confirmed

    if (!isTestCaseConfirmed(testCase.case_status)) {
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

    // produce unique IDs for comments textarea and file upload fields
    row.find('textarea')[0].id = `comment-for-testcase-${testCase.id}`;
    row.find('input[type="file"]')[0].id = `file-upload-for-testcase-${testCase.id}`;

    return row;
}

function getTestCaseExpandArea(row, testCase, permissions) {
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

    // load components
    const componentTemplate = row.find('.js-testcase-expand-components').find('template')[0].content;
    jsonRPC('Component.filter', {cases: testCase.id}, function(result) {
        result.forEach(function(element) {
            const newComponent = componentTemplate.cloneNode(true);
            $(newComponent).find('span').html(element.name);
            row.find('.js-testcase-expand-components').append(newComponent);
        });
    });

    // load tags
    const tagTemplate = row.find('.js-testcase-expand-tags').find('template')[0].content;
    jsonRPC('Tag.filter', {case: testCase.id}, function(result) {
        const uniqueTags = []

        result.forEach(function(element) {
            if (uniqueTags.indexOf(element.name) === -1) {
                uniqueTags.push(element.name)

                const newTag = tagTemplate.cloneNode(true);
                $(newTag).find('span').html(element.name);
                row.find('.js-testcase-expand-tags').append(newTag);
            }
        });
    });

    // render previous comments
    renderCommentsForObject(
        testCase.id,
        'TestCase.comments',
        'TestCase.remove_comment',
        !isTestCaseConfirmed(testCase.case_status) && permissions['perm-delete-comment'],
        row.find('.comments'),
    )

    // render comments form
    const commentFormTextArea = row.find('.js-comment-form-textarea');
    if (!isTestCaseConfirmed(testCase.case_status) && permissions['perm-add-comment']) {
        const textArea = row.find('textarea')[0];
        const fileUpload = row.find('input[type="file"]')
        const editor = initSimpleMDE(textArea, $(fileUpload), textArea.id)

        row.find('.js-post-comment').click(function(event) {
            event.preventDefault();
            const input = editor.value().trim()

            if (input) {
                jsonRPC('TestCase.add_comment', [testCase.id, input], comment => {
                    editor.value('')

                    // show the newly added comment and bind its delete button
                    row.find('.comments').append(
                        renderCommentHTML(
                            1+row.find('.js-comment-container').length,
                            comment,
                            $('template#comment-template')[0],
                            function(parentNode) {
                                bindDeleteCommentButton(
                                    testCase.id,
                                    'TestCase.remove_comment',
                                    permissions['perm-delete-comment'], // b/c we already know it's unconfirmed
                                    parentNode)
                            })
                    )
                })
            }
        });
    } else {
        commentFormTextArea.hide();
    }
}

function attachEvents(testPlanId, permissions) {
    treeViewBind('#testcases-list');

    if (permissions['perm-change-testcase']) {
        // update default tester
        $('.js-test-case-menu-tester').click(function(ev) {
            $(this).parents('.dropdown').toggleClass('open');

            var emailOrUsername = window.prompt($('#test_plan_pk').data('trans-username-email-prompt'));
            if (!emailOrUsername) {
                return false;
            }

            updateTestCasesViaAPI([getCaseIdFromEvent(ev)], {default_tester: emailOrUsername},
                                  testPlanId, permissions);

            return false;
        });


        $('.js-test-case-menu-priority').click(function(ev) {
            $(this).parents('.dropdown').toggleClass('open');

            updateTestCasesViaAPI([getCaseIdFromEvent(ev)], {priority: ev.target.dataset.id},
                                  testPlanId, permissions);
            return false;
        });

        $('.js-test-case-menu-status').click(function(ev) {
            $(this).parents('.dropdown').toggleClass('open');
            const testCaseId = getCaseIdFromEvent(ev);
            updateTestCasesViaAPI([testCaseId], {case_status: ev.target.dataset.id},
                                  testPlanId, permissions);
            return false;
        });
    }

    if (permissions['perm-remove-testcase']) {
        // delete testcase from the plan
        $('.js-test-case-menu-delete').click(function(ev) {
            $(this).parents('.dropdown').toggleClass('open');
            const testCaseId = getCaseIdFromEvent(ev);

            jsonRPC('TestPlan.remove_case', [testPlanId, testCaseId], function() {
                delete allTestCases[testCaseId];

                // fadeOut the row then remove it from the dom, if we remove it directly the user may not see the change
                $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`).fadeOut(fadeAnimationTime, function() {
                    $(this).remove();
                });
            });

            return false;
        });
    }

    // get details and draw expand area only on expand
    $('.js-testcase-row').click(function(ev) {
        // don't trigger row expansion when kebab menu is clicked
        if($(ev.target).is('button, a, input, .fa-ellipsis-v')) {
            return;
        }

        const testCaseId = getCaseIdFromEvent(ev);

        // tc was expanded once, dom is ready
        if (expandedTestCaseIds.indexOf(testCaseId) > -1) {
            return;
        }

        const tcRow = $(ev.target).closest(`[data-testcase-pk=${testCaseId}]`);
        expandedTestCaseIds.push(testCaseId);
        getTestCaseExpandArea(tcRow, allTestCases[testCaseId], permissions);
    });


    let inputs = $('.js-testcase-row').find('input');
    inputs.click(function(ev) {
        // stop trigerring row.click()
        ev.stopPropagation();
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

function updateTestCasesViaAPI(testCaseIds, updateQuery, testPlanId, permissions) {
    testCaseIds.forEach(function(caseId) {
        jsonRPC('TestCase.update', [caseId, updateQuery], function(updatedTC) {
            const testCaseRow = $(`.js-testcase-row[data-testcase-pk=${caseId}]`);

            // update internal data
            sortkey = allTestCases[caseId].sortkey;
            allTestCases[caseId] = updatedTC;
            // note: updatedTC doesn't have sortkey information
            allTestCases[caseId].sortkey = sortkey;

            animate(testCaseRow, function() {
                redrawSingleRow(caseId, testPlanId, permissions);
            });
        });
    });
}

function toolbarEvents(testPlanId, permissions) {
    $('.js-checkbox-toolbar').click(function(ev) {
        const isChecked = ev.target.checked;
        const testCaseRows = $('.js-testcase-row').find('input');

        testCaseRows.each(function(index, tc) {
            tc.checked = isChecked;
        });
    });

    $('.js-toolbar-filter-options li').click(function(ev) {
        return changeDropdownSelectedItem(
            '.js-toolbar-filter-options',
            '#input-filter-button',
            ev.target,
            $('#toolbar-filter')
        );
    });

    $('#toolbar-filter').on("keyup", function() {
        let filterValue = $(this).val().toLowerCase();
        let filterBy = $('.js-toolbar-filter-options .selected')[0].dataset.filterType;

        filterTestCasesByProperty(
            testPlanId,
            Object.values(allTestCases),
            filterBy,
            filterValue
        );
    });

    $('.js-toolbar-sort-options li').click(function(ev) {
        changeDropdownSelectedItem('.js-toolbar-sort-options', '#sort-button', ev.target);

        sortTestCases(Object.values(allTestCases), testPlanId, permissions);
        return false;
    });

    //handle asc desc icon
    $('.js-toolbar-sorting-order > span').click(function(ev) {
        let icon = $(this);

        icon.siblings('.hidden').removeClass('hidden');
        icon.addClass('hidden');

        sortTestCases(Object.values(allTestCases), testPlanId, permissions);
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
        $(this).parents('.dropdown').toggleClass('open');
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
        }

        updateTestCasesViaAPI(selectedCases, {priority: ev.target.dataset.id},
                              testPlanId, permissions);

        return false;
    });

    $('.js-toolbar-status').click(function(ev) {
        $(this).parents('.dropdown').toggleClass('open');
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
        }

        updateTestCasesViaAPI(selectedCases, {case_status: ev.target.dataset.id},
                              testPlanId, permissions);
        return false;
    });

    $('#default-tester-button').click(function(ev) {
        $(this).parents('.dropdown').toggleClass('open');
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
        }

        var emailOrUsername = window.prompt($('#test_plan_pk').data('trans-username-email-prompt'));

        if (!emailOrUsername) {
            return false;
        }

        updateTestCasesViaAPI(selectedCases, {default_tester: emailOrUsername},
                              testPlanId, permissions);

        return false;
    });

    $('#bulk-reviewer-button').click(function(ev) {
        $(this).parents('.dropdown').toggleClass('open');
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
        }

        var emailOrUsername = window.prompt($('#test_plan_pk').data('trans-username-email-prompt'));

        if (!emailOrUsername) {
            return false;
        }

        updateTestCasesViaAPI(selectedCases, {reviewer: emailOrUsername},
                              testPlanId, permissions);

        return false;
    });

    $('#delete_button').click(function(ev) {
        $(this).parents('.dropdown').toggleClass('open');
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
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

        return false;
    });

    $('#bulk-clone-button').click(function() {
        $(this).parents('.dropdown').toggleClass('open');
        let selectedCases = getSelectedTestCases();

        if (!selectedCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
        }

         window.location.assign(`/cases/clone?case=${selectedCases.join('&case=')}`);
    });

    $('#testplan-toolbar-newrun').click(function() {
        $(this).parents('.dropdown').toggleClass('open');
        let selectedTestCases = getSelectedTestCases();

        if (!selectedTestCases.length) {
            alert($('#test_plan_pk').data('trans-no-testcases-selected'));
            return false;
        }

        for (let i = 0; i < selectedTestCases.length; i++) {
            let status = allTestCases[selectedTestCases[i]].case_status;
            if (!isTestCaseConfirmed(status)) {
                alert($('#test_plan_pk').data('trans-cannot-create-testrun'));
                return false;
            }
        }

        window.location.assign(`/runs/new?p=${testPlanId}&c=${selectedTestCases.join('&c=')}`);
        return false;
    });
}

function isTestCaseConfirmed(status) {
    return confirmedStatuses.indexOf(Number(status)) > -1 ;
}

function sortTestCases(testCases, testPlanId, permissions, defaultSortBy = undefined) {
    let sortBy = defaultSortBy || $('.js-toolbar-sort-options .selected')[0].dataset.filterType,
        sortOrder = $('.js-toolbar-sorting-order > span:not(.hidden)').data('order');

    $('#testcases-list').html('');

    testCases.sort(function(tc1, tc2) {
        let value1 = tc1[sortBy] || "",
            value2 = tc2[sortBy] || "";

        if (Number.isInteger(value1) && Number.isInteger(value2)) {
            return (value1 - value2) * sortOrder;
        }

        return value1.toString().localeCompare(value2.toString()) * sortOrder;
    });

    // put the new order in the DOM
    drawTestCases(testCases, testPlanId, permissions);
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

function filterTestCasesByProperty(planId, testCases, filterBy, filterValue) {
    // no input => show all rows
    if (filterValue.trim().length === 0) {
        $('.js-testcase-row').show();
        return;
    }

    $('.js-testcase-row').hide();
    if (filterBy === 'component' || filterBy === 'tag') {
        let query = {plan: planId}
        query[`${filterBy}__name__icontains`] = filterValue

        jsonRPC('TestCase.filter', query, function(filtered) {
            // hide again if a previous async request showed something else
            $('.js-testcase-row').hide();
            filtered.forEach(tc => $(`[data-testcase-pk=${tc.id}]`).show());
        })
    } else {
        testCases.filter(function(tc){
            return (tc[filterBy] && tc[filterBy].toString().toLowerCase().indexOf(filterValue) > -1)
        }).forEach(tc => $(`[data-testcase-pk=${tc.id}]`).show());
    }
}
