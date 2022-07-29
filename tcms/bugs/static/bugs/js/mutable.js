$(document).ready(function () {
  $('#add_id_product').click(function () {
    return showRelatedObjectPopup(this)
  })

  $('#add_id_version').click(function () {
    return showRelatedObjectPopup(this)
  })

  $('#add_id_build').click(function () {
    return showRelatedObjectPopup(this)
  })

  $('#add_id_severity').click(function () {
    return showRelatedObjectPopup(this)
  })

  document.getElementById('id_product').onchange = function () {
    $('#id_product').selectpicker('refresh')
    populateVersion()
  }

  document.getElementById('id_version').onchange = function () {
    $('#id_version').selectpicker('refresh')
    populateBuild()
  }

  document.getElementById('id_build').onchange = function () {
    $('#id_build').selectpicker('refresh')
  }

  document.getElementById('id_severity').onchange = function () {
    $('#id_severity').selectpicker('refresh')
  }

  // initialize at the end b/c we rely on .change() event to initialize builds
  if ($('#id_version').find('option').length === 0) {
    populateVersion()
  }
})

// TODO: this entire file is mostly duplicate with testplans/js/mutable.js
function populateVersion () {
  const productId = $('#id_product').val()

  if (productId === null) {
    $('#add_id_version').addClass('disabled')
    $('#add_id_build').addClass('disabled')
  } else {
    $('#add_id_version').removeClass('disabled')
    $('#add_id_build').removeClass('disabled')
  }

  const href = $('#add_id_version')[0].href
  $('#add_id_version')[0].href = href.slice(0, href.indexOf('&product'))
  $('#add_id_version')[0].href += `&product=${productId}`
  $('#id_version').find('option').remove()
  updateVersionSelectFromProduct()
}

function populateBuild () {
  const versionId = $('#id_version').val()

  if (versionId === null) {
    $('#add_id_build').addClass('disabled')
  } else {
    $('#add_id_build').removeClass('disabled')
  }

  const href = $('#add_id_build')[0].href
  $('#add_id_build')[0].href = href.slice(0, href.indexOf('&version'))
  $('#add_id_build')[0].href += `&version=${versionId}`
  updateBuildSelectFromVersion()
}
