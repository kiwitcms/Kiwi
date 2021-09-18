$(document).ready(() => {
  $('.selectpicker').selectpicker()
  $('[data-toggle="tooltip"]').tooltip()

  loadInitialProduct(reloadCharts)

  $('#id_after').on('dp.change', reloadCharts)
  $('#id_before').on('dp.change', reloadCharts)
  document.getElementById('id_test_plan').onchange = reloadCharts
  document.getElementById('id_product').onchange = () => {
    updateTestPlanSelectFromProduct(reloadCharts)
  }
})

function reloadCharts () {
  const query = {}

  const testPlanIds = $('#id_test_plan').val()
  const productIds = $('#id_product').val()

  if (testPlanIds.length) {
    query.plan__in = testPlanIds
  } else if (productIds.length) {
    query.case__category__product_id__in = productIds
  }

  const dateBefore = $('#id_before')
  if (dateBefore.val()) {
    query.create_date__lte = dateBefore.data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
  }

  const dateAfter = $('#id_after')
  if (dateAfter.val()) {
    query.create_date__gte = dateAfter.data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
  }

  jsonRPC('Management.performance', query, result => {
    console.log(result)

    // the actual result is in the same format, only it can be much bigger
    // and the chart may break
    // const r = {
    //   1: {
    //     "asankov": 1,
    //     "atodorov": 2
    //   },
    //   2: {
    //     "asankov": 1,
    //     "atodorov": 2
    //   },
    //   3: {
    //     "asankov": 1,
    //     "atodorov": 1,
    //     "": 1
    //   },
    //   4: {
    //     "asankov": 1,
    //     "atodorov": 1
    //   },
    //   5: {
    //     "asankov": 5,
    //     "atodorov": 2,
    //     "bot": 1
    //   }
    // }

    drawChart(result)
  }, true)
}

function drawChart (data) {
  // the X axis of the chart - run IDs
  const groupedCategories = []
  // map of username -> table column. we use map here for faster lookup by username.
  const groupedColumnsDataMap = {}
  const usernames = new Set()

  // collect all the testers so that we know how much columns we will have
  Object.entries(data).forEach(([_testRunId, asigneeCount]) => {
    Object.entries(asigneeCount).forEach(([username, _executionCount]) => {
      // filter empty users
      // TODO: maybe we can do that on the API level
      if (username) {
        usernames.add(username)
      }
    })
  })

  usernames.forEach(username => (groupedColumnsDataMap[username] = [username]))

  Object.entries(data).forEach(([testRunId, _asigneeCount]) => {
    groupedCategories.push(`TR-${testRunId}`)

    const asigneesCount = data[testRunId]

    // for each user in the groupedColumnsDataMap check if that user
    // is assigned any executions for this run.
    Object.entries(groupedColumnsDataMap).forEach(([username, data]) => {
      const count = asigneesCount[username]
      if (count) {
        data.push(count)
      } else {
        // TODO: find a way to hide the 0 valued-columns
        data.push(0)
      }
    })
  })

  // C3 does not need a map, but an array of values
  // get rid of the keys, because we do not need them anymore
  const groupedColumnsData = Object.values(groupedColumnsDataMap)

  const chartConfig = $().c3ChartDefaults().getDefaultGroupedBarConfig()
  chartConfig.bindto = '#performance-chart'
  chartConfig.axis = {
    x: {
      categories: groupedCategories,
      type: 'category'
    },
    y: {
      tick: {
        format: showOnlyRoundNumbers
      }
    }
  }
  chartConfig.data = {
    type: 'bar',
    columns: groupedColumnsData
  }
  chartConfig.zoom = {
    enabled: true
  }
  c3.generate(chartConfig)
}
