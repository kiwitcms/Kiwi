function loadInitialProduct (callback = () => {}) {
  jsonRPC('Product.filter', {}, data => {
    updateSelect(data, '#id_product', 'id', 'name', null)
    callback()
  })
}

function showOnlyRoundNumbers (number) {
  return number % 1 === 0 ? number : ''
}

// Close multiselect list when selecting an item
// Iterate over all dropdown lists
$('select[multiple]').each(function () {
  $(this).on('change', function () {
    $(this).parent('.bootstrap-select').removeClass('open')
  })
})
