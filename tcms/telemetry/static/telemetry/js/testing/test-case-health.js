$(document).ready(() => {
    $('[data-toggle="tooltip"]').tooltip()

    loadInitialProduct();
    loadInitialTestPlans();

    document.getElementById('id_product').onchange = () => {
        update_version_select_from_product();
        update_build_select_from_product(true);
        updateTestPlanSelectFromProduct(drawPage);
    };

    document.getElementById('id_version').onchange = drawPage;
    document.getElementById('id_build').onchange = drawPage;
    document.getElementById('id_test_plan').onchange = drawPage;

    $('#id_after').on('dp.change', drawPage);
    $('#id_before').on('dp.change', drawPage);

    drawPage();
})

function drawPage() {
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

    jsonRPC("Testing.test_case_health", query, data => {
        drawTable('#test-case-health-table', data);
    })
}

function drawTable(selector, data) {
    $(`${selector} > tbody`).remove()

    $(selector).DataTable({
        data: data,
        columns: [
            {
                data: null,
                render: renderTestCaseColumn
            },
            {
                data: null,
                render: renderFailedExecutionsColumn
            },
            {
                data: null,
                render: renderPercentColumn
            },
        ],
        paging: false,
        ordering: false,
        dom: "t"
    });
}

function renderTestCaseColumn(data) {
    return `<a href="/case/${data.id}">TC-${data.id}</a>: ${data.case_summary}`;
}

function renderFailedExecutionsColumn(data) {
    return `${data.count.fail} of ${data.count.all}`;
}

// TODO: this can be moved to the back-end and provide the percentage there
function renderPercentColumn(data) {
    return Number.parseFloat(data.count.fail / data.count.all * 100).toFixed(1);
}
