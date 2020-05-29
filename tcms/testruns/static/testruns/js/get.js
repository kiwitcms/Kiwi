$(document).ready(() => {

    $('.bootstrap-switch').bootstrapSwitch();

    const testRunId = $('#test_run_pk').data('pk')

    $('#status_button').on('switchChange.bootstrapSwitch', (_event, state) => {
        if (state) {
            jsonRPC('TestRun.update', [testRunId, { 'stop_date': null }], () => {
                $('.stop-date').html('-')
            })
        } else {
            const timeZone = $('#clock').data('time-zone')
            const now = currentTimeWithTimezone(timeZone)

            jsonRPC('TestRun.update', [testRunId, { 'stop_date': now }], testRun => {
                const stopDate = moment(testRun.stop_date).format("DD MMM YYYY, HH:mm a")
                $('.stop-date').html(stopDate)
            })
        }
    });

    const permRemoveTag = $('#test_run_pk').data('perm-remove-tag') === 'True';

    // bind everything in tags table
    tagsCard('TestRun', testRunId, { run: testRunId }, permRemoveTag);

    jsonRPC('TestExecutionStatus.filter', {}, executionStatuses => {
        jsonRPC('TestExecution.filter', { 'run_id': testRunId }, testExecutions => {
            drawPercentBar(testExecutions, executionStatuses)
            renderTestExecutions(testExecutions, executionStatuses)
        })
    })
})


function drawPercentBar(testExecutions, executionStatuses) {
    let positiveCount = 0;
    let negativeCount = 0;
    let allCount = testExecutions.length;
    let statusCount = {}
    executionStatuses.forEach(s => statusCount[s.name] = { count: 0, id: s.id })

    testExecutions.forEach(testExecution => {
        const executionStatus = executionStatuses.find(s => s.id === testExecution.status_id)

        if (executionStatus.weight > 0) {
            positiveCount++
        } else if (executionStatus.weight < 0) {
            negativeCount++
        }

        statusCount[executionStatus.name].count++
    })

    renderProgressBars(positiveCount, negativeCount, allCount)
    renderCountPerStatusList(statusCount)
}

function renderProgressBars(positiveCount, negativeCount, allCount) {

    const positivePercent = +(positiveCount / allCount * 100).toFixed(2)
    const positiveBar = $(".progress > .progress-completed")
    if (positivePercent) {
        positiveBar.text(`${positivePercent}%`)
    }
    positiveBar.css('width', `${positivePercent}%`)
    positiveBar.attr('aria-valuenow', `${positivePercent}`)

    const negativePercent = +(negativeCount / allCount * 100).toFixed(2)
    const negativeBar = $('.progress > .progress-failed')
    if (negativePercent) {
        negativeBar.text(`${negativePercent}%`)
    }
    negativeBar.css('width', `${negativePercent}%`)
    negativeBar.attr('aria-valuenow', `${negativePercent}`)

    const neutralPercent = +(100 - (negativePercent + positivePercent)).toFixed(2)
    const neutralBar = $('.progress > .progress-bar-remaining')
    if (neutralPercent) {
        neutralBar.text(`${neutralPercent}%`)
    }
    neutralBar.css('width', `${neutralPercent}%`)
    neutralBar.attr('aria-valuenow', `${neutralPercent}`)

    $(".total-execution-count").text(allCount)
}

function renderCountPerStatusList(statusCount) {
    for (var status in statusCount) {
        const statusId = statusCount[status].id;

        $(`#count-for-status-${statusId}`).attr('href', `?status_id=${statusId}`).text(statusCount[status].count);
    }
}

function renderTestExecutions(testExecutions, executionStatuses) {
    const container = $('#test-executions-container')
    const testExecutionRowTemplate = $('#test-execution-row')[0].content

    const testCaseIds = []
    testExecutions.forEach(testExecution => {
        testCaseIds.push(testExecution.case_id)

        const executionStatus = executionStatuses.find(status => status.id === testExecution.status_id)
        const template = $(testExecutionRowTemplate.cloneNode(true))

        container.append(renderTestExecutionRow(template, testExecution, executionStatus))
    })

    treeViewBind();
    renderAdditionalInformation(testExecutions, testCaseIds)
}

function renderAdditionalInformation(testExecutions, testExecutionCaseIds) {
    jsonRPC('TestCase.filter', { 'id__in': testExecutionCaseIds }, testCases => {
        testExecutions.forEach(testExecution => {
            const testCase = testCases.find(testCase => testCase.id === testExecution.case_id)

            const listGroupItem = $(`.test-execution-${testExecution.id}`)
            listGroupItem.find('.test-execution-priority').html(testCase.priority)
            listGroupItem.find('.test-execution-category').html(testCase.category)
            listGroupItem.find('.test-execution-text').html(testCase.text)
            listGroupItem.find('.test-execution-notes').append(testCase.notes)

            const isAutomatedElement = listGroupItem.find('.test-execution-automated')
            const isAutomatedIcon = testCase.is_automated ? 'fa-cog' : 'fa-thumbs-up'
            const isAutomatedAttr = testCase.is_automated ? isAutomatedElement.data('automated') : isAutomatedElement.data('manual')
            isAutomatedElement.addClass(isAutomatedIcon)
            isAutomatedElement.attr('title', isAutomatedAttr)

            jsonRPC('TestExecution.get_links', { 'execution_id': testExecution.id, 'is_defect': true }, bugs => {
                listGroupItem.find('.test-execution-bugs-count').html(bugs.length)
            })
        })
    })

}

function renderTestExecutionRow(template, testExecution, testExecutionStatus) {
    template.find('.list-group-item').addClass(`test-execution-${testExecution.id}`)
    template.find('.test-execution-info').html(`TE-${testExecution.id}`)
    template.find('.test-execution-info-link').html(testExecution.case)
    template.find('.test-execution-info-link').attr('href', `/case/${testExecution.case_id}/`)
    template.find('.test-execution-tester').html(testExecution.tested_by || '-')
    template.find('.test-execution-asignee').html(testExecution.assignee || '-')

    template.find('.test-execution-status-icon').addClass(testExecutionStatus.icon).css('color', testExecutionStatus.color)
    template.find('.test-execution-status-name').html(testExecutionStatus.name).css('color', testExecutionStatus.color)

    return template
}


/////// the functions below were used in bulk-menu actions
/////// and need updates before they can be used again
///////
function changeExecutionAssignee() {
  const executions = 0 // todo: this is the list of all selected executions
  if (!executions.length) {
    window.alert(default_messages.alert.no_case_selected);
    return false;
  }
//todo: all texts in alert/prompt must come translated from the HTML template
  var assignee = window.prompt('Please type new email or username for assignee');
  if (!assignee) {
    return false;
  }
  executions.forEach(execution_id => jsonRPC('TestExecution.update', [execution_id, {'assignee': assignee}], () => { }, sync=true));
  window.location.reload();
}

function updateExecutionText() {
  const executions = 0 // todo: this is the list of all selected executions
  if (!executions.length) {
    window.alert(default_messages.alert.no_case_selected);
    return false;
  }
//todo: translations
  executions.forEach(executionId =>
    jsonRPC('TestExecution.update', [executionId, {'case_text_version': 'latest'}], () => { }, sync=true)
  );
  window.location.reload(true);
}

function fileBugFromExecution(run_id, title_container, container, case_id, execution_id) {
  // todo: this dialog needs to be reimplemented with a Patternfly modal
  var dialog = new AddIssueDialog({
    'action': 'Report',
    'onSubmit': function (e, dialog) {
      e.stopPropagation();
      e.preventDefault();

        var tracker_id = dialog.get_data()['bug_system_id'];
        jsonRPC('Bug.report', [execution_id, tracker_id], function(result) {
            $('#dialog').hide();

            if (result.rc === 0) {
                // unescape b/c Issue #1533
                const target_url = result.response.replace(/&amp;/g, '&')
                window.open(target_url, '_blank');
            } else {
                window.alert(result.response);
            }
      });
    }
  });

  dialog.show();
}
