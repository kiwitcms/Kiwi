/**
 * Remove a Bug from TestCase or TestExecution object by hitting
 * the backend API.
 *
 * @param {String} id - Bug ID
 * @param {Number} case_id - TestCase ID
 * @param {Number} case_run_id - TestExecution ID or empty/undefined
 */
function removeCaseBug(id, case_id, case_run_id) {
    if(!window.confirm('Are you sure?')) {
        return false;
    }

    var params = {bug_id: id};
    let row_selector = `#bug_${id}_${case_id}_${case_run_id}`;

    if(case_run_id) {
        params['case_run_id'] = case_run_id;
    } else {
        params['case_id'] = case_id;
        params['case_run__isnull'] = true;
    }

    var callback = function(data) {
        $(row_selector).hide();
        $(row_selector).parents('li#bug_item').hide();
    }

    jsonRPC('Bug.remove', [params], callback);
}
