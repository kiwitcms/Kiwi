$(document).ready(function() {
    const testPlanId = $('#test_plan_pk').data('testplanPk');
    const testCases = {
        'confirmed': [],
        'not_confirmed': []
    };

    // bind everything in tags table
    const perm_remove_tag = $('#test_plan_pk').data('perm-remove-tag') === 'True';
    tagsCard('TestPlan', testPlanId, {plan: testPlanId}, perm_remove_tag);

    jsonRPC('TestCase.filter', [{'plan': testPlanId}], function(data) {
        for (var i = 0; i < data.length; i++) {
            var testCase = data[i];
            //todo: refactor when testcase_status is replaced with boolean flag
            if (testCase.case_status_id === 2) {
                testCases.confirmed.push(data[i]);
            } else {
                testCases.not_confirmed.push(data[i]);
            }
        }
        drawTestCases(testCases.confirmed);
        treeViewBind();
    });

});

function drawTestCases(testCases) {
    var container = $('#confirmed-testcases'),
        noCasesTemplate = $('#no_test_cases'),
        testCaseRow = $('#test_case_row')[0],
        testCaseSummary = $(testCaseRow.content).find('.list-view-pf-main-info a.testcase')[0];

    if (testCases.length > 0) {
        for (var i = 0; i < testCases.length; i++) {
            var testCase = testCases[i];
            testCaseSummary.innerHTML = getTestCaseRowContent(testCase);
            container.append($(testCaseRow).html());
        }
    } else {
        container.append(noCasesTemplate[0].innerHTML);
    }
}


function getTestCaseRowContent(testCase) {
    var rowDetailsTemplate = $('#test_case_row_details')[0],
        row = $(rowDetailsTemplate.content);

    row.find('.js-test-case-link').html(`TC-${testCase.id}: ${testCase.summary}`).attr('href',`/case/${testCase.id}/`);
    row.find('.js-test-case-priority').html(`${testCase.priority}`);
    row.find('.js-test-case-category').html(`${testCase.category}`);
    row.find('.js-test-case-author').html(`${testCase.author}`);
    row.find('.js-test-case-tester').html(`${testCase.default_tester || '-'}`);
    return $(rowDetailsTemplate).html();
}
