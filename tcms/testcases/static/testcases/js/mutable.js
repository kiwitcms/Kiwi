$(document).ready(function () {
  $('#text_templates').change(function () {
    markdownEditor.codemirror.setValue($(this).val())
  })

  if ($('#id_category').find('option').length === 0) {
    populateProductCategory()
  }

  $('#add_id_product').click(function () {
    return showRelatedObjectPopup(this)
  })

  $('#add_id_category').click(function () {
    return showRelatedObjectPopup(this)
  })

  document.getElementById('id_product').onchange = function () {
    $('#id_product').selectpicker('refresh')
    populateProductCategory()
  }

  document.getElementById('id_category').onchange = function () {
    $('#id_category').selectpicker('refresh')
  }

  $('.selectpicker').selectpicker()
  $('.bootstrap-switch').bootstrapSwitch()
})

function populateProductCategory () {
  const productId = $('#id_product').val()

  if (productId === null) {
    $('#add_id_category').addClass('disabled')
  } else {
    $('#add_id_category').removeClass('disabled')
  }

  const href = $('#add_id_category')[0].href
  $('#add_id_category')[0].href = href.slice(0, href.indexOf('&product'))
  $('#add_id_category')[0].href += `&product=${productId}`
  $('#id_category').find('option').remove()
  updateCategorySelectFromProduct()
}
