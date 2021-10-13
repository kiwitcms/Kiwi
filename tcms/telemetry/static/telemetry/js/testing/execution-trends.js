$(document).ready(() => {
  $('[data-toggle="tooltip"]').tooltip()

  loadInitialProduct()

  document.getElementById('id_product').onchange = () => {
    updateVersionSelectFromProduct()
    // note: don't pass drawChart as callback to avoid calling it twice
    // b/c update_version_select... triggers .onchange()
    updateTestPlanSelectFromProduct()
  }

  document.getElementById('id_version').onchange = () => {
    drawChart()
    updateBuildSelectFromVersion(true)
  }
  document.getElementById('id_build').onchange = drawChart
  document.getElementById('id_test_plan').onchange = drawChart

  $('#id_after').on('dp.change', drawChart)
  $('#id_before').on('dp.change', drawChart)

  drawChart()
})

function drawChart () {
  const query = {}

  const productIds = $('#id_product').val()
  if (productIds.length) {
    query.run__plan__product__in = productIds
  }

  const versionIds = $('#id_version').val()
  if (versionIds.length) {
    query.run__plan__product_version__in = versionIds
  }

  const buildIds = $('#id_build').val()
  if (buildIds.length) {
    query.build_id__in = buildIds
  }

  const testPlanIds = $('#id_test_plan').val()
  if (testPlanIds.length) {
    query.run__plan__in = testPlanIds
  }

  const dateBefore = $('#id_before')
  if (dateBefore.val()) {
    query.stop_date__lte = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
  }

  const dateAfter = $('#id_after')
  if (dateAfter.val()) {
    query.stop_date__gte = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
  }

  const totalKey = $('.main').data('total-key')

  jsonRPC('Testing.execution_trends', query, data => {
    drawPassingRateSummary(data.status_count)

    const chartData = Object.entries(data.data_set).map(entry => [entry[0], ...entry[1]])
    const categories = data.categories.map(testRunId => `TR-${testRunId}`)

    $('#chart > svg').remove()

    const c3ChartDefaults = $().c3ChartDefaults()
    const config = c3ChartDefaults.getDefaultAreaConfig()
    config.axis = {
      x: {
        categories: categories,
        type: 'category',
        tick: {
          fit: false,
          multiline: false
        }
      },
      y: {
        tick: {
          format: showOnlyRoundNumbers
        }
      }
    }
    config.bindto = '#chart'
    config.color = {
      pattern: data.colors
    }
    config.data = {
      columns: chartData,
      type: 'area-spline',
      order: null
    }
    config.bar = {
      width: {
        ratio: 1
      }
    }
    config.tooltip = {
      format: {
        value: (value, _ratio, _id, _index) => value || undefined
      }
    }
    config.legend = {
      hide: [totalKey]
    }
    c3.generate(config)

    // hide the total data point
    $(`.c3-target-${totalKey}`).addClass('hidden')
  })
}

function drawPassingRateSummary (statusCount) {
  const allCount = statusCount.positive + statusCount.negative + statusCount.neutral
  $('.passing-rate-summary .total').text(allCount)

  const positivePercent = statusCount.positive ? roundDown(statusCount.positive / allCount * 100) : 0
  const positiveBar = $('.progress > .progress-bar-success')
  const positiveRateText = `${positivePercent}%`
  positiveBar.css('width', positiveRateText)
  positiveBar.text(positiveRateText)
  $('.passing-rate-summary .positive').text(statusCount.positive)

  const neutralPercent = statusCount.neutral ? roundDown(statusCount.neutral / allCount * 100) : 0
  const neutralRateText = `${neutralPercent}%`
  const neutralBar = $('.progress > .progress-bar-remaining')
  neutralBar.css('width', neutralRateText)
  neutralBar.text(neutralRateText)
  $('.passing-rate-summary .neutral').text(statusCount.neutral)

  const negativePercent = statusCount.negative ? roundDown(statusCount.negative / allCount * 100) : 0
  const negativeRateText = `${negativePercent}%`
  const negativeBar = $('.progress > .progress-bar-danger')
  negativeBar.css('width', negativeRateText)
  negativeBar.text(negativeRateText)
  $('.passing-rate-summary .negative').text(statusCount.negative)
}

// we need this function, because the standard library does not have
// one that rounds the number down, which means that the sum
// of the percents may become more than 100% and that breaksg the chart
function roundDown (number) {
  return Math.floor(number * 100) / 100
}
