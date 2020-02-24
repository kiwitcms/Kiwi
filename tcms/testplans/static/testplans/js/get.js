$(document).ready(function() {
    const testPlanId = $('#test_plan_pk').data('testplanPk');
    const testCases = {
        'confirmed': [],
        'not_confirmed': []
    };

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
        drawConfirmedTestCases();

    });

    function drawConfirmedTestCases() {
        var container = $('#confirmed-testcases'),
            noCasesTemplate = $('#no_test_cases'),
            testCaseRow = $('#test_case_row')[0],
            testCaseMainInfo = $(testCaseRow.content).find('.list-view-pf-main-info')[0];

        if (testCases.confirmed.length > 0) {
            for (var i = 0; i < testCases.confirmed.length; i++) {
                var testCase = testCases.confirmed[i];
                testCaseMainInfo.innerHTML = `<a href="/case/${testCase.id}">TC-${testCase.id}: ${testCase.summary}</a>`;
                container.append($(testCaseRow).html());
            }
        } else {
            container.append(noCasesTemplate[0].innerHTML);
        }

        treeViewBind();
    }
});
