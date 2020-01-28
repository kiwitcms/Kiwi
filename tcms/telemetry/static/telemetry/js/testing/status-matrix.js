let table;
let initial_column = {
    data: null,
    className: "table-view-pf-actions",
    render: function (data, type, full, meta) {
        const caseId = data.tc_id;

        return `<span style="padding: 5px;">` +
            `<a href="/case/${caseId}">TC-${caseId}: ${data.tc_summary}</a>` +
            `</span>`;
    }
};

$(document).ready(() => {
    $('[data-toggle="tooltip"]').tooltip()

    loadInitialProduct();
    loadInitialTestPlans();

    document.getElementById('id_product').onchange = () => {
        update_version_select_from_product();
        update_build_select_from_product(true);
        updateTestPlanSelectFromProduct(drawTable);
    };

    document.getElementById('id_version').onchange = drawTable;
    document.getElementById('id_build').onchange = drawTable;
    document.getElementById('id_test_plan').onchange = drawTable;

    $('#id_after').on('dp.change', drawTable);
    $('#id_before').on('dp.change', drawTable);

    drawTable();
});


function drawTable() {
    if (table) {
        table.destroy();

        $('table > thead > tr > th:not(.header)').remove();
        $('table > tbody > tr').remove();
    }

    const query = {};

    const productId = $('#id_product').val();
    if (productId) {
        query['run__plan__product'] = productId;
    }

    const versionId = $('#id_version').val();
    if (versionId) {
        query['run__plan__product_version'] = versionId;
    }

    const buildId = $('#id_build').val();
    if (buildId) {
        query['build_id'] = buildId;
    }

    const testPlanId = $('#id_test_plan').val();
    if (testPlanId) {
        query['run__plan__pk'] = testPlanId;
    }

    const dateBefore = $('#id_before');
    if (dateBefore.val()) {
        query['close_date__lte'] = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
    }

    const dateAfter = $('#id_after');
    if (dateAfter.val()) {
        query['close_date__gte'] = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
    }

    jsonRPC('Testing.status_matrix', query, data => {

        const table_columns = [initial_column];

        Object.keys(data.columns).forEach(testRunId => {
            const testRunSummary = data.columns[testRunId];
            $('.table > thead > tr').append(`<th>TR-${testRunId} ${testRunSummary}</th>`);

            table_columns.push({
                data: null,
                sortable: false,
                render: renderData(testRunId)
            });
        });

        table = $('#table').DataTable({
            columns: table_columns,
            data: data.data,
            paging: false,
            ordering: false,
            dom: "t"
        });

        const cells = $('.table > tbody > tr > td:has(.execution-status)');
        Object.entries(cells).forEach(applyStyleToCell);
    });
}

function applyStyleToCell(cell) {
    const cellElement = cell[1];
    if (cellElement) {
        const cellChildren = cellElement.children;
        if (cellChildren) {
            const el = cellChildren[0];
            if (el && el.attributes['color']) {
                color = el.attributes['color'].nodeValue
                $(cell[1]).attr('style', `border-left: 5px solid ${color}`);
            }
        }
    }
}

function renderData(testRunId) {
    return (data, type, full, meta) => {
        const execution = full.executions.find(e => e.run_id === Number(testRunId));
        if (execution) {
            return `<span class="execution-status" color="${execution.color}">` +
                `<a href="/runs/${execution.run_id}/#caserun_${execution.pk}">TE-${execution.pk}</a>` +
                `</span>`;
        }
        return '';
    }
}
