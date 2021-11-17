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

// https://gist.github.com/iperelivskiy/4110988#gistcomment-2697447
// used only to hash strings to get unique IDs for href targets
function funhash (s) {
  let h = 0xdeadbeef
  for (let i = 0; i < s.length; i++) {
    h = Math.imul(h ^ s.charCodeAt(i), 2654435761)
  }
  return (h ^ h >>> 16) >>> 0
}

function displayProperties (selector) {
  const caseId = $('#test_case_pk').data('pk')
  const container = $(selector)
  const propertyTemplate = $('#property-fragment')[0].content
  const valueTemplate = $(propertyTemplate).find('template')[0].content
  const shownProperties = []
  let property = null

  jsonRPC('TestCase.properties', { case: caseId }, data => {
    data.forEach(element => {
      if (!shownProperties.includes(element.name)) {
        property = $(propertyTemplate.cloneNode(true))
        property.find('.js-property-name').html(element.name)

        const collapseId = 'collapse' + funhash(element.name)
        property.find('.js-property-name').attr('href', `#${collapseId}`)
        property.find('.js-panel-collapse').attr('id', collapseId)
        property.find('.js-remove-property').attr('data-case_id', element.case)
        property.find('.js-remove-property').attr('data-property-name', element.name)
        property.find('template').remove()

        container.find('.js-insert-here').append(property)
        shownProperties.push(element.name)
      }

      const value = $(valueTemplate.cloneNode(true))
      value.find('.js-property-value').text(element.value)
      value.find('.js-remove-value').attr('data-id', element.id)
      container.find('.js-panel-body').last().append(value)
    })

    $('.js-remove-property').click(function () {
      const sender = $(this)
      jsonRPC(
        'TestCase.remove_property',
        { case: sender.data('case_id'), name: sender.data('property-name') },
        function (data) {
          sender.parents('.panel').first().fadeOut(500)
        }
      )
      return false
    })

    $('.js-remove-value').click(function () {
      const sender = $(this)
      jsonRPC('TestCase.remove_property', { pk: sender.data('id') }, function (data) {
        sender.parent().fadeOut(500)
      })
      return false
    })
  })
}

function addPropertyValue () {
  const caseId = $('#test_case_pk').data('pk')
  const nameValue = $('#property-value-input').val().split('=')

  jsonRPC(
    'TestCase.add_property',
    [caseId, nameValue[0], nameValue[1]],
    function (data) {
      animate($('.js-insert-here'), function () {
        $('#property-value-input').val('')
        $('.js-insert-here').empty()
        displayProperties('#properties-accordion')
      })
    }
  )
}

$(document).ready(function () {
  const caseId = $('#test_case_pk').data('pk')
  const productId = $('#product_pk').data('pk')
  const permRemoveTag = $('#test_case_pk').data('perm-remove-tag') === 'True'
  const permRemoveComponent = $('#test_case_pk').data('perm-remove-component') === 'True'
  const permRemovePlan = $('#test_case_pk').data('perm-remove-plan') === 'True'

  displayProperties('#properties-accordion')
  $('.js-add-property-value').click(function () {
    addPropertyValue()
    return false
  })

  $('#property-value-input').keyup(function (event) {
    if (event.keyCode === 13) {
      addPropertyValue()
    }
  })

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
