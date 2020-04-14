let executionStatuses;

$(document).ready(() => {

    $('.bootstrap-switch').bootstrapSwitch();

    const testRunId = $('#test_run_pk').data('pk')

    $('#status_button').on('switchChange.bootstrapSwitch', (_event, state) => {
        if (state) {
            jsonRPC('TestRun.update', [testRunId, { 'stop_date': null }], () => { })
        } else {
            const timeZone = $('#clock').data('time-zone')
            const now = currentTimeWithTimezone(timeZone)

            jsonRPC('TestRun.update', [testRunId, { 'stop_date': now }], () => { })
        }
    });

    const permRemoveTag = $('#test_run_pk').data('perm-remove-tag') === 'True';

    // bind everything in tags table
    tagsCard('TestRun', testRunId, { run: testRunId }, permRemoveTag);

    jsonRPC('TestExecutionStatus.filter', {}, data => {
        executionStatuses = data
        drawPercentBar(testRunId)
    })
})


function drawPercentBar(testRunId) {

    jsonRPC('TestExecution.filter', { 'run_id': testRunId }, testExecutions => {

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
    })
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
        const status_id = statusCount[status].id;

        $(`#count-for-status-${status_id}`).attr('href', `?status_id=${status_id}`);
        $(`#count-for-status-${status_id}`).text(statusCount[status].count);
    }
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
