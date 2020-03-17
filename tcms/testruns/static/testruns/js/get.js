$(document).ready(() => {

    $('.bootstrap-switch').bootstrapSwitch();

    const testRunId = $('#test_run_pk').data('pk')

    $('#status_button').on('switchChange.bootstrapSwitch', (_event, state) => {
        if (state) {
            jsonRPC('TestRun.update', [testRunId, { 'stop_date': null }], () => { })
        } else {
            let now = new Date().toISOString().replace("T", " ")
            now = now.slice(0, now.length-5)
            jsonRPC('TestRun.update', [testRunId, { 'stop_date': now }], () => { })
        }
    });

    const permRemoveTag = $('#test_run_pk').data('perm-remove-tag') === 'True';

    // bind everything in tags table
    tagsCard('TestRun', testRunId, { run: testRunId }, permRemoveTag);
})
