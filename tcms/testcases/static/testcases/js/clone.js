export function pageTestcasesCloneReadyHandler () {
    if ($('#page-testcases-clone').length === 0) {
        return
    }

    $('.bootstrap-switch').bootstrapSwitch()
}
