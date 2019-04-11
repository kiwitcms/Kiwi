$(document).ready(() => {
    $('.selectpicker').selectpicker();

    loadInitialProduct();

    document.getElementById('id_select_product').onchange = updateTestPlanSelect;
    document.getElementById('id_select_test_plan').onchange = reloadCharts;
});

function loadInitialProduct() {
    jsonRPC('Product.filter', {}, data => {
        updateSelect(data, '#id_select_product', 'id', 'name');
        reloadCharts();
    });
}

function updateTestPlanSelect() {
    const productId = $('#id_select_product').val();

    if (!productId) {
        updateSelect([], '#id_select_test_plan', 'plan_id', 'name');
        reloadCharts();
        return;
    }
    jsonRPC('TestPlan.filter', {'product_id': productId}, data => {
        updateSelect(data, '#id_select_test_plan', 'plan_id', 'name');
        reloadCharts();
    })
}

function reloadCharts() {
    const query = {};

    const testPlanId = $('#id_select_test_plan').val();
    const productId = $('#id_select_product').val();

    if (testPlanId) {
        query['plan'] = testPlanId;
    } else if (productId) {
        query['category__product_id'] = productId;
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

    const automatedPercent = count.automated / count.all * 100;

    d3.select('.automated-bar')
        .attr('aria-valuenow', `${automatedPercent}`)
        .attr('title', `${count.automated} Automated`)
        .style('width', `${automatedPercent}%`);

    $('.automated-bar').tooltip();

    const manualPercent = count.manual / count.all * 100;

    d3.select('.manual-bar')
        .attr('aria-valuenow', `${manualPercent}`)
        .attr('title', `${count.manual} Manual`)
        .style('width', `${manualPercent}%`);

    $('.manual-bar').tooltip();
}

function drawPrioritiesChart(priorities) {
    drawChart(priorities, 'priority', '#priorities-chart');
}

function drawCategoriesChart(categories) {
    drawChart(categories, 'category', '#categories-chart');
}

function drawChart(data, type, selector) {
    const names = [];
    const values = [[type]];
    data.forEach(c => {
        names.push(c[0]);
        values[0].push(c[1]);
    });

    let chartConfig = $().c3ChartDefaults().getDefaultBarConfig(names);
    chartConfig.bindto = selector;
    chartConfig.axis = {
        x: {
            categories: names,
            type: 'category',
        },
        y: {
            tick: {
                format: showOnlyRoundNumbers
            }
        }
    };
    chartConfig.data = {
        type: 'bar',
        columns: values,
    };
    chartConfig.grid = {
        show: false
    };

    c3.generate(chartConfig);
}

function showOnlyRoundNumbers(number) {
    if (number % 1 === 0) {
        return number;
    }
    return '';
}
