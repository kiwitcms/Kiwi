// https://gist.github.com/iperelivskiy/4110988#gistcomment-2697447
// used only to hash strings to get unique IDs for href targets
function funhash (s) {
  let h = 0xdeadbeef
  for (let i = 0; i < s.length; i++) {
    h = Math.imul(h ^ s.charCodeAt(i), 2654435761)
  }
  return (h ^ h >>> 16) >>> 0
}

function displayProperties (objectId, objectAttrName, viewMethod, removeMethod) {
  const container = $('#properties-accordion')
  const propertyTemplate = $('#property-fragment')[0].content
  const valueTemplate = $(propertyTemplate).find('template')[0].content
  const shownProperties = []
  let property = null

  const query = {}
  query[objectAttrName] = objectId

  jsonRPC(viewMethod, query, data => {
    data.forEach(element => {
      if (!shownProperties.includes(element.name)) {
        property = $(propertyTemplate.cloneNode(true))
        property.find('.js-property-name').html(element.name)

        const collapseId = 'collapse' + funhash(element.name)
        property.find('.js-property-name').attr('href', `#${collapseId}`)
        property.find('.js-panel-collapse').attr('id', collapseId)
        property.find('.js-remove-property').attr(`data-${objectAttrName}_id`, element[objectAttrName])
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
      const query = { name: sender.data('property-name') }
      query[objectAttrName] = sender.data(`${objectAttrName}_id`)

      jsonRPC(removeMethod, query, function (data) {
        sender.parents('.panel').first().fadeOut(500)
      }
      )
      return false
    })

    $('.js-remove-value').click(function () {
      const sender = $(this)
      jsonRPC(removeMethod, { pk: sender.data('id') }, function (data) {
        sender.parent().fadeOut(500)
      })
      return false
    })
  })
}

function addPropertyValue (objectId, objectAttrName, viewMethod, addMethod, removeMethod) {
  const nameValue = $('#property-value-input').val().split('=')

  jsonRPC(
    addMethod,
    [objectId, nameValue[0], nameValue[1]],
    function (data) {
      animate($('.js-insert-here'), function () {
        $('#property-value-input').val('')
        $('.js-insert-here').empty()

        displayProperties(objectId, objectAttrName, viewMethod, removeMethod)
      })
    }
  )
}

// binds everything in this card
function propertiesCard (objectId, objectAttrName, viewMethod, addMethod, removeMethod) {
  displayProperties(objectId, objectAttrName, viewMethod, removeMethod)

  $('.js-add-property-value').click(function () {
    addPropertyValue(objectId, objectAttrName, viewMethod, addMethod, removeMethod)
    return false
  })

  $('#property-value-input').keyup(function (event) {
    if (event.keyCode === 13) {
      addPropertyValue(objectId, objectAttrName, viewMethod, addMethod, removeMethod)
    }
  })
}
