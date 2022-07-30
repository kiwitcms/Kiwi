
$(document).ready(function () {
  const table = $('#resultsTable').DataTable({
    pageLength: $('#navbar').data('defaultpagesize'),
    ajax: function (data, callback, settings) {
      const params = {}

      if ($('#id_summary').val()) {
        params.summary__icontains = $('#id_summary').val()
      }

      if ($('#id_severity').val()) {
        params.severity = $('#id_severity').val()
      };

      if ($('#id_product').val()) {
        params.product = $('#id_product').val()
      };

      if ($('#id_version').val()) {
        params.version = $('#id_version').val()
      };

      if ($('#id_build').val()) {
        params.build = $('#id_build').val()
      };

      if ($('#id_reporter').val()) {
        params.reporter__username__startswith = $('#id_reporter').val()
      };

      if ($('#id_assignee').val()) {
        params.assignee__username__startswith = $('#id_assignee').val()
      };

      if ($('#id_before').val()) {
        params.created_at__lte = $('#id_before').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
      }

      if ($('#id_after').val()) {
        params.created_at__gte = $('#id_after').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
      }

      params.status = $('#id_status').is(':checked')

      dataTableJsonRPC('Bug.filter', params, callback)
    },
    columns: [
      { data: 'pk' },
      {
        data: null,
        render: function (data, type, full, meta) {
          if (data.severity__name) {
            return `<span class="${data.severity__icon}" style="color: ${data.severity__color}"></span> ${data.severity__name}`
          }

          return ''
        }
      },
      {
        data: null,
        render: function (data, type, full, meta) {
          return '<a href="/bugs/' + data.pk + '/" target="_parent">' + escapeHTML(data.summary) + '</a>'
        }
      },
      { data: 'created_at' },
      { data: 'product__name' },
      { data: 'version__value' },
      { data: 'build__name' },
      { data: 'reporter__username' },
      { data: 'assignee__username' }
    ],
    dom: 't',
    language: {
      loadingRecords: '<div class="spinner spinner-lg"></div>',
      processing: '<div class="spinner spinner-lg"></div>',
      zeroRecords: 'No records found'
    },
    order: [[0, 'asc']]
  })

  hookIntoPagination('#resultsTable', table)

  $('#btn_search').click(function () {
    table.ajax.reload()
    return false // so we don't actually send the form
  })

  $('#id_product').change(function () {
    updateVersionSelectFromProduct()
  })

  $('#id_version').change(function () {
    updateBuildSelectFromVersion(true)
  })

  $('.bootstrap-switch').bootstrapSwitch()

  $('.selectpicker').selectpicker()
})
