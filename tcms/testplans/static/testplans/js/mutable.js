/*
    Used in mutable.html and clone.html
*/
$(document).ready((function () {
    if ($('#id_version').find('option').length === 0) {
        populateProductVersion();
    }

    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this);
    });

    $('#add_id_version').click(function () {
        return showRelatedObjectPopup(this);
    });

    $('.selectpicker').selectpicker();

    $('.bootstrap-switch').bootstrapSwitch();

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh');
        populateProductVersion();
    };

    document.getElementById('id_version').onchange = function () {
        $('#id_version').selectpicker('refresh');
    }
}));

function populateProductVersion() {
    let href = $('#add_id_version')[0].href;
    $('#add_id_version')[0].href = href.slice(0, href.indexOf('&product'));
    $('#add_id_version')[0].href += `&product=${$('#id_product').val()}`;

    $('#id_version').find('option').remove();

    update_version_select_from_product();
}
