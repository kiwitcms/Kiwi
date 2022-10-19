$(() => {
  if ($('#page-testcases-mutable').length === 0) {
    return
  }

  $('#text_templates').change(function () {
    markdownEditor.codemirror.setValue($(this).val())
  })

  if ($('#id_category').find('option').length === 0) {
    populateCategory()
  }

  $('#add_id_product').click(function () {
    return showRelatedObjectPopup(this)
  })

  $('#add_id_category').click(function () {
    return showRelatedObjectPopup(this)
  })

  document.getElementById('id_product').onchange = function () {
    $('#id_product').selectpicker('refresh')
    populateCategory()
  }

  document.getElementById('id_category').onchange = function () {
    $('#id_category').selectpicker('refresh')
  }

  $('.selectpicker').selectpicker()
  $('.bootstrap-switch').bootstrapSwitch()
})
