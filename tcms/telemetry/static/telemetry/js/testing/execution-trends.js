$(document).ready(() => {
    $('[data-toggle="tooltip"]').tooltip()

    loadInitialProduct();

    document.getElementById('id_product').onchange = () => {
        update_version_select_from_product();
        // note: don't pass drawChart as callback to avoid calling it twice
        // b/c update_version_select... triggers .onchange()
        updateTestPlanSelectFromProduct();
    };

    document.getElementById('id_version').onchange = () => {
        drawChart();
        update_build_select_from_version(true);
    }
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
        query['run__plan__pk'] = testPlanId;
    }

    const dateBefore = $('#id_before');
    if (dateBefore.val()) {
        query['stop_date__lte'] = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
    }

    const dateAfter = $('#id_after');
    if (dateAfter.val()) {
        query['stop_date__gte'] = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
    }

    const totalKey = $('.main').data('total-key')

    jsonRPC('Testing.execution_trends', query, data => {
        drawPassingRateSummary(data.status_count)

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
        config.tooltip = {
            format: {
                value: (value, _ratio, _id, _index) => value ? value : undefined
            }
        }
        config.legend = {
            hide: [totalKey],
        }
        c3.generate(config);

        // hide the total data point
        $(`.c3-target-${totalKey}`).addClass('hidden')
    });
}

function drawPassingRateSummary(status_count) {
    const allCount = status_count.positive + status_count.negative + status_count.neutral
    $('.passing-rate-summary .total').text(allCount)

    const positivePercent = status_count.positive ? roundDown(status_count.positive / allCount * 100) : 0
    const positiveBar = $('.progress > .progress-bar-success')
    const positiveRateText = `${positivePercent}%`
    positiveBar.css('width', positiveRateText)
    positiveBar.text(positiveRateText)
    $('.passing-rate-summary .positive').text(status_count.positive)

    const neutralPercent = status_count.neutral ? roundDown(status_count.neutral / allCount * 100) : 0
    const neutralRateText = `${neutralPercent}%`
    const neutralBar = $('.progress > .progress-bar-remaining')
    neutralBar.css('width', neutralRateText)
    neutralBar.text(neutralRateText)
    $('.passing-rate-summary .neutral').text(status_count.neutral)

    const negativePercent = status_count.negative ? roundDown(status_count.negative / allCount * 100) : 0
    const negativeRateText = `${negativePercent}%`
    const negativeBar = $('.progress > .progress-bar-danger')
    negativeBar.css('width', negativeRateText)
    negativeBar.text(negativeRateText)
    $('.passing-rate-summary .negative').text(status_count.negative)
}

// we need this function, because the standard library does not have
// one that rounds the number down, which means that the sum
// of the percents may become more than 100% and that breaksg the chart
function roundDown(number) {
    return Math.floor(number * 100) / 100
}
