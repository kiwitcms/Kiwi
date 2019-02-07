$(document).ready((function () {
    if ($('#id_category').find('option').length === 0) {
        populateProductCategory();
    }

    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this);
    });

    $('#add_id_category').click(function () {
        return showRelatedObjectPopup(this);
    });

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh');
        populateProductCategory();
    };

    document.getElementById('id_category').onchange = function () {
        $('#id_category').selectpicker('refresh');
    };

    $('.selectpicker').selectpicker();
    $('.bootstrap-switch').bootstrapSwitch();
}));

function populateProductCategory() {
    let href = $('#add_id_category')[0].href;
    $('#add_id_category')[0].href = href.slice(0, href.indexOf('&product'));
    $('#add_id_category')[0].href += `&product=${$('#id_product').val()}`;

    $('#id_category').find('option').remove();

    update_category_select_from_product();
}
