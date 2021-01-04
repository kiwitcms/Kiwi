$(document).ready(() => {
    $('.selectpicker').selectpicker();
    $('[data-toggle="tooltip"]').tooltip()

    loadInitialProduct(reloadCharts);

    $('#id_after').on('dp.change', reloadCharts);
    $('#id_before').on('dp.change', reloadCharts);
    document.getElementById('id_test_plan').onchange = reloadCharts;
    document.getElementById('id_product').onchange = () => {
        updateTestPlanSelectFromProduct(reloadCharts);
    };

    // not relevant in this context
    $('#version_and_build').hide();
});

function reloadCharts() {
    const query = {};

    const testPlanId = $('#id_test_plan').val();
    const productId = $('#id_product').val();

    if (testPlanId) {
        query['plan'] = testPlanId;
    } else if (productId) {
        query['category__product_id'] = productId;
    }

    const dateBefore = $('#id_before');
    if (dateBefore.val()) {
        query['create_date__lte'] = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
    }

    const dateAfter = $('#id_after');
    if (dateAfter.val()) {
        query['create_date__gte'] = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
    }

    jsonRPC('Testing.breakdown', query, result => {
        drawAutomatedBar(result.count);
        drawPrioritiesChart(result.priorities);
        drawCategoriesChart(result.categories);
    }, true);
}

function drawAutomatedBar(count) {
    d3.select('#total-count')
        .style('font-weight', 'bold')
        .style('font-size', '18px')
        .text(count.all);

    d3.selectAll('.progress-bar')
        .attr('aria-valuemin', '0')
        .attr('aria-valuemax', '100');

    d3.select('.automated-legend-text > span').remove();
    d3.select('.manual-legend-text > span').remove();

    d3.select('.automated-legend-text')
        .append('span')
        .text(` - ${count.automated}`);

    d3.select('.manual-legend-text')
        .append('span')
        .text(` - ${count.manual}`);

    const automatedPercent = count.automated / count.all * 100;

    d3.select('.automated-bar')
        .attr('aria-valuenow', `${automatedPercent}`)
        .attr('title', `${count.automated} Automated`)
        .style('width', `${automatedPercent}%`);

    const manualPercent = count.manual / count.all * 100;

    d3.select('.manual-bar')
        .attr('aria-valuenow', `${manualPercent}`)
        .attr('title', `${count.manual} Manual`)
        .style('width', `${manualPercent}%`);
}

function drawPrioritiesChart(priorities) {
    drawChart(priorities, 'priority', '#priorities-chart');
}

function drawCategoriesChart(categories) {
    drawChart(categories, 'category', '#categories-chart');
}

function drawChart(data, type, selector) {
    const categories = new Set();
    let groups = [[]];
    let chartData = [];

    Object.values(data).forEach(entry => {
        Object.keys(entry).forEach(key => categories.add(key));
    });

    Object.entries(data).forEach(entry => {
        let group = entry[0];
        groups[0].push(group);

        let dataEntry = [group];

        categories.forEach(cat => {
            let count = entry[1][cat];
            if (!count) {
                count = 0;
            }
            dataEntry.push(count);
        });

        chartData.push(dataEntry);
    });

    let chartConfig = $().c3ChartDefaults().getDefaultStackedBarConfig();
    chartConfig.bindto = selector;
    chartConfig.axis = {
        x: {
            categories: Array.from(categories),
            type: 'category',
        },
        y: {
            tick: {
                format: showOnlyRoundNumbers
            }
        }
    };
    chartConfig.data = {
        columns: chartData,
        groups: groups,
        type: 'bar',
        order: null
    };
    chartConfig.color = {
        pattern: [
            $.pfPaletteColors.blue,
            $.pfPaletteColors.red100,
        ]
    };
    chartConfig.grid = {
        show: false
    };

    c3.generate(chartConfig);
}
