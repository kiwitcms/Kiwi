$(document).ready(() => {
    $('[data-toggle="tooltip"]').tooltip()

    loadInitialProduct();
    loadInitialTestPlans();

    document.getElementById('id_product').onchange = () => {
        update_version_select_from_product();
        update_build_select_from_product(true);
        updateTestPlanSelectFromProduct(drawChart);
    };

    document.getElementById('id_version').onchange = drawChart;
    document.getElementById('id_build').onchange = drawChart;
    document.getElementById('id_test_plan').onchange = drawChart;

    $('#id_after').on('dp.change', drawChart);
    $('#id_before').on('dp.change', drawChart);

    drawChart();
});

function drawChart() {
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
        query['run__plan__plan_id'] = testPlanId;
    }

    const dateBefore = $('#id_before');
    if (dateBefore.val()) {
        query['close_date__lte'] = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
    }

    const dateAfter = $('#id_after');
    if (dateAfter.val()) {
        query['close_date__gte'] = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
    }

    jsonRPC('Testing.execution_trends', query, data => {
        const chartData = Object.entries(data.data_set).map(entry => [entry[0], ...entry[1]]);
        const categories = data.categories.map(testRunId => `TR-${testRunId}`);

        $('#chart > svg').remove();

        const c3ChartDefaults = $().c3ChartDefaults();
        const config = c3ChartDefaults.getDefaultAreaConfig();
        config.axis = {
            x: {
                categories: categories,
                type: 'category',
                tick: {
                    fit: false,
                    multiline: false,
                },
            },
            y: {
                tick: {
                    format: showOnlyRoundNumbers
                }
            }
        };
        config.bindto = '#chart';
        config.color = {
            pattern: data.colors
        };
        config.data = {
            columns: chartData,
            type: 'area-spline',
            order: null
        };
        config.bar = {
            width: {
                ratio: 1
            }
        };
        c3.generate(config);
    });
}
