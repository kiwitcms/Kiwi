$(document).ready(() => {
  $('[data-toggle="tooltip"]').tooltip()

  loadInitialProduct()

  document.getElementById('id_product').onchange = () => {
    updateVersionSelectFromProduct()
    // note: don't pass drawPage as callback to avoid calling it twice
    // b/c update_version_select... triggers .onchange()
    updateTestPlanSelectFromProduct()
  }

  document.getElementById('id_version').onchange = () => {
    drawPage()
    updateBuildSelectFromVersion(true)
  }

  document.getElementById('id_build').onchange = drawPage
  document.getElementById('id_test_plan').onchange = drawPage

  $('#id_after').on('dp.change', drawPage)
  $('#id_before').on('dp.change', drawPage)

  drawPage()
})

function drawPage () {
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

  jsonRPC('Testing.test_case_health', query, data => {
    drawTable('#test-case-health-table', data)
  })
}

function drawTable (selector, data) {
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
        render: renderVisualPercent
      },
      {
        data: null,
        render: renderFailedExecutionsColumn
      },
      {
        data: null,
        render: renderPercentColumn
      }
    ],
    paging: false,
    ordering: false,
    dom: 't'
  })
}

function renderTestCaseColumn (data) {
  return `<a href="/case/${data.case_id}">TC-${data.case_id}</a>: ${data.case_summary}`
}

function renderFailedExecutionsColumn (data) {
  return `${data.count.fail} / ${data.count.all}`
}

// TODO: this can be moved to the back-end and provide the percentage there
function renderPercentColumn (data) {
  return Number.parseFloat(data.count.fail / data.count.all * 100).toFixed(1)
}

function renderVisualPercent (data) {
  const failPercent = data.count.fail / data.count.all * 100

  const colors = []
  const step = 20
  for (i = 0; i < 5; i++) {
    if (failPercent > i * step) {
      colors.push('#cc0000') // pf-red-100
    } else {
      colors.push('#3f9c35') // pf-green-400
    }
  }

  return colors.reduce((prev, color) => prev + `<span class='visual-percent-box' style='background-color: ${color}'></span>\n`, '')
}
