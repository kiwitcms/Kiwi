const planCache = {}

function addComponent (objectId, _input, toTable) {
  const _name = _input.value

  if (_name.length > 0) {
    jsonRPC('TestCase.add_component', [objectId, _name], function (data) {
      if (data !== undefined) {
        toTable.row.add({ name: data.name, id: data.id }).draw()
        $(_input).val('')
      } else {
        $(_input).parents('div.input-group').addClass('has-error')
      }
    })
  }
}

function addTestPlanToTestCase (caseId, plansTable) {
  const planName = $('#input-add-plan')[0].value
  const plan = planCache[planName]

  jsonRPC('TestPlan.add_case', [plan.id, caseId], function (data) {
    plansTable.row.add({
      id: plan.id,
      name: plan.name,
      author__username: plan.author__username,
      type__name: plan.type__name,
      product__name: plan.product__name
    }).draw()
    $('#input-add-plan').val('')
  })
}

function initAddPlan (caseId, plansTable) {
  // + button
  $('#btn-add-plan').click(function () {
    addTestPlanToTestCase(caseId, plansTable)
  })

  // Enter key
  $('#input-add-plan').keyup(function (event) {
    if (event.keyCode === 13) {
      addTestPlanToTestCase(caseId, plansTable)
    };
  })

  // autocomplete
  $('#input-add-plan.typeahead').typeahead({
    minLength: 1,
    highlight: true
  }, {
    name: 'plans-autocomplete',
    // will display up to X results even if more were returned
    limit: 100,
    async: true,
    display: function (element) {
      const displayName = 'TP-' + element.id + ': ' + element.name
      planCache[displayName] = element
      return displayName
    },
    source: function (query, processSync, processAsync) {
      // accepts "TP-1234" or "tp-1234" or "1234"
      query = query.toLowerCase().replace('tp-', '')
      if (query === '') {
        return
      }

      let rpcQuery = { pk: query }

      // or arbitrary string
      if (isNaN(query)) {
        if (query.length >= 3) {
          rpcQuery = { name__icontains: query }
        } else {
          return
        }
      }

      jsonRPC('TestPlan.filter', rpcQuery, function (data) {
        return processAsync(data)
      })
    }
  })
}

$(document).ready(function () {
  const caseId = $('#test_case_pk').data('pk')
  const productId = $('#product_pk').data('pk')
  const permRemoveTag = $('#test_case_pk').data('perm-remove-tag') === 'True'
  const permRemoveComponent = $('#test_case_pk').data('perm-remove-component') === 'True'
  const permRemovePlan = $('#test_case_pk').data('perm-remove-plan') === 'True'

  propertiesCard(caseId, 'case', 'TestCase.properties', 'TestCase.add_property', 'TestCase.remove_property')

  // bind everything in tags table
  tagsCard('TestCase', caseId, { case: caseId }, permRemoveTag)

  // components table
  const componentsTable = $('#components').DataTable({
    ajax: function (data, callback, settings) {
      dataTableJsonRPC('Component.filter', [{ cases: caseId }], callback)
    },
    columns: [
      { data: 'name' },
      {
        data: 'id',
        sortable: false,
        render: function (data, type, full, meta) {
          if (permRemoveComponent) {
            return '<a href="#components" class="remove-component" data-pk="' + data + '"><span class="pficon-error-circle-o"></span></a>'
          }
          return ''
        }
      }
    ],
    dom: 't',
    language: {
      loadingRecords: '<div class="spinner spinner-lg"></div>',
      processing: '<div class="spinner spinner-lg"></div>',
      zeroRecords: 'No records found'
    },
    order: [[0, 'asc']]
  })

  // remove component button
  componentsTable.on('draw', function () {
    $('.remove-component').click(function () {
      const tr = $(this).parents('tr')

      jsonRPC('TestCase.remove_component', [caseId, $(this).data('pk')], function (data) {
        componentsTable.row($(tr)).remove().draw()
      })
    })
  })

  // add component button and Enter key
  $('#add-component').click(function () {
    addComponent(caseId, $('#id_components')[0], componentsTable)
  })

  $('#id_components').keyup(function (event) {
    if (event.keyCode === 13) {
      addComponent(caseId, $('#id_components')[0], componentsTable)
    };
  })

  // components autocomplete
  $('#id_components.typeahead').typeahead({
    minLength: 3,
    highlight: true
  }, {
    name: 'components-autocomplete',
    // will display up to X results even if more were returned
    limit: 100,
    async: true,
    display: function (element) {
      return element.name
    },
    source: function (query, processSync, processAsync) {
      jsonRPC('Component.filter', { name__icontains: query, product: productId }, function (data) {
        data = arrayToDict(data)
        return processAsync(Object.values(data))
      })
    }
  })

  // testplans table
  const plansTable = $('#plans').DataTable({
    ajax: function (data, callback, settings) {
      dataTableJsonRPC('TestPlan.filter', { cases: caseId }, callback)
    },
    columns: [
      { data: 'id' },
      {
        data: null,
        render: function (data, type, full, meta) {
          return '<a href="/plan/' + data.id + '/">' + escapeHTML(data.name) + '</a>'
        }
      },
      { data: 'author__username' },
      { data: 'type__name' },
      { data: 'product__name' },
      {
        data: null,
        sortable: false,
        render: function (data, type, full, meta) {
          if (permRemovePlan) {
            return '<a href="#plans" class="remove-plan" data-pk="' + data.id + '"><span class="pficon-error-circle-o"></span></a>'
          }
          return ''
        }
      }
    ],
    dom: 't',
    language: {
      loadingRecords: '<div class="spinner spinner-lg"></div>',
      processing: '<div class="spinner spinner-lg"></div>',
      zeroRecords: 'No records found'
    },
    order: [[0, 'asc']]
  })

  // remove plan button
  plansTable.on('draw', function () {
    $('.remove-plan').click(function () {
      const tr = $(this).parents('tr')

      jsonRPC('TestPlan.remove_case', [$(this).data('pk'), caseId], function (data) {
        plansTable.row($(tr)).remove().draw()
      })
    })
  })

  // bind add TP to TC widget
  initAddPlan(caseId, plansTable)

  // bugs table
  loadBugs('.bugs', {
    execution__case: caseId,
    is_defect: true
  })

  // executions treeview
  treeViewBind()
})
