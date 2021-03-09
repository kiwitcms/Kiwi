function loadInitialProduct(callback = () => {}) {
    jsonRPC('Product.filter', {}, data => {
        updateSelect(data, '#id_product', 'id', 'name');
        callback();
    });
}

function showOnlyRoundNumbers(number) {
    return number % 1 === 0 ? number : '';
}
