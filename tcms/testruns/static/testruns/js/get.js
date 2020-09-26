let testExecutionStatuses = {}

$(document).ready(() => {

    $('.bootstrap-switch').bootstrapSwitch();
    $('.selectpicker').selectpicker();

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

    $('.add-hyperlink-bulk').click(() => {
        const selected = selectedCheckboxes()
        if ($.isEmptyObject(selected)) {
            return false
        }

        addLinkToExecutions(selected.executionIds)
    })

    $('.remove-case-bulk').click(() => {
        const selected = selectedCheckboxes()
        if ($.isEmptyObject(selected)) {
            return false
        }

        const areYouSureText = $('#test_run_pk').data('trans-are-you-sure')
        if (confirm(areYouSureText)) {
            removeCases(testRunId, selected.caseIds)
        }
    })

    $('.change-assignee-bulk').click(changeAssigneeBulk)
    $('.update-case-text-bulk').click(updateCaseText)

    $('.bulk-change-status').click(function () {
        // `this` is the clicked link
        const statusId = $(this).data('status-id')
        changeStatusBulk(statusId)

        // close dropdown
        $('.statuses-dropdown').removeClass('open')

        // so that we don't follow the link
        return false
    })

    const permRemoveTag = $('#test_run_pk').data('perm-remove-tag') === 'True';

    // bind everything in tags table
    tagsCard('TestRun', testRunId, { run: testRunId }, permRemoveTag);

    jsonRPC('TestExecutionStatus.filter', {}, executionStatuses => {
        testExecutionStatuses = executionStatuses

        jsonRPC('TestExecution.filter', { 'run_id': testRunId }, testExecutions => {
            drawPercentBar(testExecutions, executionStatuses)
            renderTestExecutions(testExecutions)
        })
    })

    $('.bulk-select-checkbox').click(event => {
        const isChecked = event.target.checked;
        const testExecutionSelectors = $('#test-executions-container').find('.test-execution-checkbox');

        testExecutionSelectors.each((_index, te) => { te.checked = isChecked });
    });
})

function selectedCheckboxes() {
    const allSelected = $('.test-execution-checkbox:checked')

    if (!allSelected.length) {
        const warningText = $('#test_run_pk').data('trans-no-executions-selected')
        alert(warningText)

        return {}
    }

    const testCaseIds = []
    const testExecutionIds = []
    allSelected.each((_index, checkbox) => {
        checkbox = $(checkbox)

        const testExecutionId = checkbox.data('test-execution-id')
        testExecutionIds.push(testExecutionId)

        const testCaseId = checkbox.data('test-execution-case-id')
        testCaseIds.push(testCaseId)
    })

    return {
        caseIds: testCaseIds,
        executionIds: testExecutionIds,
    }
}

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

function renderTestExecutions(testExecutions) {
    const container = $('#test-executions-container')

    const testCaseIds = []
    testExecutions.forEach(testExecution => {
        testCaseIds.push(testExecution.case_id)

        container.append(renderTestExecutionRow(testExecution))
    })

    treeViewBind();
    renderAdditionalInformation(testExecutions, testCaseIds)
}

function renderAdditionalInformation(testExecutions, testExecutionCaseIds) {
    $('.test-executions-count').html(testExecutions.length);

    renderTestCaseInformation(testExecutions, testExecutionCaseIds)
}

function renderTestCaseInformation(testExecutions, testExecutionCaseIds) {
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

            jsonRPC('TestExecution.get_links', { 'execution_id': testExecution.id }, links => {
                const bugCount = links.filter(link => link.is_defect).length;
                listGroupItem.find('.test-execution-bugs-count').html(bugCount)

                listGroupItem.find('.add-link-button').click(() => addLinkToExecutions([testExecution.id]))
                listGroupItem.find('.one-click-bug-report-button').click(() => fileBugFromExecution(testExecution))

                const ul = listGroupItem.find('.test-execution-hyperlinks')
                links.forEach(link => ul.append(renderLink(link)))
            })

            jsonRPC('TestCase.list_attachments', [testCase.id], attachments => {
                const ul = listGroupItem.find(`.test-case-attachments`)

                if (!attachments.length) {
                    ul.find('.hidden').removeClass('hidden')
                    return;
                }

                const liTemplate = $('#attachments-list-item')[0].content

                attachments.forEach(attachment => {
                    const li = liTemplate.cloneNode(true)
                    const attachmentLink = $(li).find('a')[0]

                    attachmentLink.href = attachment.url
                    attachmentLink.innerText = attachment.url.split('/').slice(-1)[0]
                    ul.append(li)
                })
            })
        })
    })

}

function renderTestExecutionRow(testExecution) {
    const testExecutionRowTemplate = $('#test-execution-row')[0].content
    const template = $(testExecutionRowTemplate.cloneNode(true))

    template.find('.test-execution-checkbox').data('test-execution-id', testExecution.id)
    template.find('.test-execution-checkbox').data('test-execution-case-id', testExecution.case_id)
    template.find('.test-execution-element').addClass(`test-execution-${testExecution.id}`)
    template.find('.test-execution-element').addClass(`test-execution-case-${testExecution.case_id}`)
    template.find('.test-execution-info').html(`TE-${testExecution.id}`)
    template.find('.test-execution-info-link').html(testExecution.case)
    template.find('.test-execution-info-link').attr('href', `/case/${testExecution.case_id}/`)
    template.find('.test-execution-tester').html(testExecution.tested_by || '-')
    template.find('.test-execution-asignee').html(testExecution.assignee || '-')
    template.find('.test-execution-information .run-date').html(testExecution.close_date || '-')
    template.find('.test-execution-information .build').html(testExecution.build)
    template.find('.test-execution-information .text-version').html(testExecution.case_text_version)

    const testExecutionStatus = testExecutionStatuses.find(status => status.id === testExecution.status_id)

    template.find('.test-execution-status-icon').addClass(testExecutionStatus.icon).css('color', testExecutionStatus.color)
    template.find('.test-execution-status-name').html(testExecutionStatus.name).css('color', testExecutionStatus.color)

    return template
}

function changeStatusBulk(statusId) {
    const selected = selectedCheckboxes()
    if ($.isEmptyObject(selected)) {
        return false
    }

    selected.executionIds.forEach(executionId => {
        jsonRPC('TestExecution.update', [executionId, {
            'status': statusId,
        }], execution => {
            reloadRowFor(execution)
        })
    });
}

function reloadRowFor(execution) {
    const testExecutionRow = $(`.test-execution-${execution.id}`)
    animate(testExecutionRow, () => {
        testExecutionRow.replaceWith(renderTestExecutionRow(execution))

        treeViewBind()
        renderTestCaseInformation([execution], [execution.case_id])
    })
}

/////// the functions below were used in bulk-menu actions
/////// and need updates before they can be used again
///////
function changeAssigneeBulk() {
    const selected = selectedCheckboxes()
    if ($.isEmptyObject(selected)) {
        return false
    }

    const enterAssigneeText = $('#test_run_pk').data('trans-enter-assignee-name-or-email')
    const assignee = prompt(enterAssigneeText)

    if (!assignee) {
        return false;
    }
    selected.executionIds.forEach(executionId => {
        jsonRPC('TestExecution.update', [executionId, { 'assignee': assignee }], execution => {
            const testExecutionRow = $(`div.list-group-item.test-execution-${executionId}`);
            animate(testExecutionRow, () => {
                testExecutionRow.find(`.test-execution-asignee`).html(execution.assignee)
            })
        })
    });
}

function updateCaseText() {
    const selected = selectedCheckboxes()
    if ($.isEmptyObject(selected)) {
        return false
    }

    selected.executionIds.forEach(executionId =>
        jsonRPC('TestExecution.update', [executionId, { 'case_text_version': 'latest' }], execution => {
            reloadRowFor(execution)
        })
    );
}

function fileBugFromExecution(execution) {

    // remove all previous event handlers
    $('.one-click-bug-report-form').off('submit')

    // this handler must be here, because if we bind it when the page is loaded.
    // we have no way of knowing for what execution ID the form is submitted for.
    $('.one-click-bug-report-form').submit(() => {
        const trackerId = $('.one-click-bug-report-form #id-issue-tracker').val()
        jsonRPC('Bug.report', [execution.id, trackerId], result => {

            // close the modal
            $('#one-click-bug-report-modal button.close').click()

            if (result.rc !== 0) {
                alert(result.response)
                return
            }

            reloadRowFor(execution)

            // unescape b/c Issue #1533
            const targetUrl = result.response.replace(/&amp;/g, '&')
            window.open(targetUrl, '_blank')
        })
        return false
    })

    return true // so that the modal is opened
}

function addLinkToExecutions(testExecutionIDs) {
    // remove all previous event handlers
    $('.add-hyperlink-form').off('submit')

    // this handler must be here, because if we bind it when the page is loaded.
    // we have no way of knowing for what execution ID the form is submitted for.
    $('.add-hyperlink-form').submit(() => {
        const url = $('.add-hyperlink-form #id_url').val()
        const name = $('.add-hyperlink-form #id_name').val()
        const isDefect = $('.add-hyperlink-form #defectCheckbox').is(':checked')
        const updateTracker = true

        testExecutionIDs.forEach(testExecutionId => {
            jsonRPC('TestExecution.add_link', [{
                execution_id: testExecutionId,
                url: url,
                name: name,
                is_defect: isDefect,
            }, updateTracker], link => {
                const testExecutionRow = $(`div.list-group-item.test-execution-${testExecutionId}`);
                animate(testExecutionRow, () => {
                    const ul = testExecutionRow.find('.test-execution-hyperlinks')
                    ul.append(renderLink(link))
                })
            })
        })

        // clean the values
        $('.add-hyperlink-form #id_url').val('')
        $('.add-hyperlink-form #id_name').val('')
        $('.add-hyperlink-form #defectCheckbox').bootstrapSwitch('state', false)
        $('.add-hyperlink-form #autoUpdateCheckbox').bootstrapSwitch('state', false)

        // close the modal
        $('#add-link-modal button.close').click()

        return false;
    })

    return true; // so that the modal is opened
}

function renderLink(link) {
    const linkEntryTemplate = $('#link-entry')[0].content
    const template = $(linkEntryTemplate.cloneNode(true))
    if (link.is_defect) {
        template.find('.link-icon').addClass('fa fa-bug')
        const bugTooltip = template.find('.bug-tooltip')
        bugTooltip.css('visibility', 'visible')

        template.find('[data-toggle=popover]')
            .popovers()
            .on('show.bs.popover', () => fetchBugDetails({ href: link.url }, bugTooltip))
    }

    const linkUrlEl = template.find('.link-url')
    linkUrlEl.html(link.name || link.url)
    linkUrlEl.attr('href', link.url)

    return template
}

function removeCases(testRunId, testCaseIds) {
    for (const testCaseId of testCaseIds) {
        jsonRPC('TestRun.remove_case', [testRunId, testCaseId], () => {
            $(`.test-execution-case-${testCaseId}`).remove()

            const testExecutionCountEl = $('.test-executions-count')
            const count = parseInt(testExecutionCountEl[0].innerText)
            testExecutionCountEl.html(count - 1)
        }, true);
    }
}
