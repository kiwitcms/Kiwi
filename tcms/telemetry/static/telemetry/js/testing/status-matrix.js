let table;
let initial_column = {
    data: null,
    className: "table-view-pf-actions",
    render: function (data, type, full, meta) {
        const caseId = data.tc_id;

        return `<span style="padding: 5px;">` +
            `<a href="/case/${caseId}/">TC-${caseId}: ${data.tc_summary}</a>` +
            `</span>`;
    }
};

$(document).ready(() => {
    $('[data-toggle="tooltip"]').tooltip()

    loadInitialProduct();

    document.getElementById('id_product').onchange = () => {
        update_version_select_from_product();
        // note: don't pass drawTable as callback to avoid calling it twice
        // b/c update_version_select... triggers .onchange()
        updateTestPlanSelectFromProduct();
    };

    document.getElementById('id_version').onchange = () => {
        drawTable();
        update_build_select_from_version(true);
    }

    document.getElementById('id_build').onchange = drawTable;
    document.getElementById('id_test_plan').onchange = drawTable;
    document.getElementById('id_order').onchange = drawTable;
    document.getElementById('id_include_child_tps').onchange = drawTable;

    $('#id_after').on('dp.change', drawTable);
    $('#id_before').on('dp.change', drawTable);

    drawTable();

    $('#table').on('draw.dt', function(){
        setMaxHeight($(this));
    })

    $('.bootstrap-switch').bootstrapSwitch();
});

$(window).on('resize', function(){
    setMaxHeight($('#table'));
});


function setMaxHeight(t) {
    const maxH = 0.99 * (window.innerHeight - t.position().top)
    t.css('max-height', maxH);
}

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

    var testPlanId = $('#id_test_plan').val();
    const includeChildTPs = $('#id_include_child_tps').is(':checked')
    if (testPlanId) {
        testPlanId = parseInt(testPlanId)
        query['run__plan__pk__in'] = [testPlanId];

        // note: executed synchronously to avoid race condition between
        // collecting the list of child TPs and drawing the table below
        if (includeChildTPs) {
            jsonRPC('TestPlan.filter', {'parent': testPlanId}, function(result) {
                result.forEach(function(element) {
                    query['run__plan__pk__in'].push(element.id);
                });
            }, true);
        }
    }

    const dateBefore = $('#id_before');
    if (dateBefore.val()) {
        query['stop_date__lte'] = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
    }

    const dateAfter = $('#id_after');
    if (dateAfter.val()) {
        query['stop_date__gte'] = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
    }

    jsonRPC('Testing.status_matrix', query, data => {
        const table_columns = [initial_column];
        const testRunIds = Object.keys(data.columns);

        // reverse the TR-xy order to show newest ones first
        if (! $('#id_order').is(':checked')) {
            testRunIds.reverse();
        }

        testRunIds.forEach(testRunId => {
            const testRunSummary = data.columns[testRunId];
            $('.table > thead > tr').append(`
            <th class="header-test-run">
                <a href="/runs/${testRunId}/">TR-${testRunId}</a>
                <span class="fa pficon-help" data-toggle="tooltip" data-placement="bottom" title="${testRunSummary}"></span>
            </th>`);

            table_columns.push({
                data: null,
                sortable: false,
                render: renderData(testRunId, testPlanId, includeChildTPs)
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

        // initialize the tooltips by hand, because they are dinamically inserted
        // and not handled by Bootstrap itself
        $('span[data-toggle=tooltip]').tooltip();
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
                if (el.attributes['from-parent'].nodeValue === "true") {
                    $(cell[1]).addClass('danger');
                }
            }
        }
    }
}

function renderData(testRunId, testPlanId, includeChildTPs) {
    return (data, type, full, meta) => {
        const execution = full.executions.find(e => e.run_id === Number(testRunId));
        if (execution) {
            const fromParentTP = includeChildTPs && (execution.plan_id === testPlanId);
            var iconClass = '';

            if (fromParentTP) {
                iconClass = "fa fa-arrow-circle-o-up";
            }

            return `<span class="execution-status ${iconClass}" color="${execution.color}" from-parent="${fromParentTP}">` +
                `<a href="/runs/${execution.run_id}/#caserun_${execution.pk}">TE-${execution.pk}</a>` +
                `</span>`;
        }
        return '';
    }
}
