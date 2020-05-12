$(document).ready(() => {

    $('.bootstrap-switch').bootstrapSwitch();

})




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
