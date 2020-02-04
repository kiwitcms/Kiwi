function updateTestPlanSelectFromProduct(callback = () => {}) {
    const updateCallback = (data = []) => {
        updateSelect(data, '#id_test_plan', 'id', 'name');
        callback();
    };

    const productId = $('#id_product').val();
    if (!productId) {
        updateCallback();
    } else {
        jsonRPC('TestPlan.filter', {product: productId}, updateCallback);
    }
}

function loadInitialProduct(callback = () => {}) {
    jsonRPC('Product.filter', {}, data => {
        updateSelect(data, '#id_product', 'id', 'name');
        callback();
    });
}

function loadInitialTestPlans() {
    jsonRPC('TestPlan.filter', {}, data => updateSelect(data, '#id_test_plan', 'id', 'name'));
}

function showOnlyRoundNumbers(number) {
    return number % 1 === 0 ? number : '';
}
