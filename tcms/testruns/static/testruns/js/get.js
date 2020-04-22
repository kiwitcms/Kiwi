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
