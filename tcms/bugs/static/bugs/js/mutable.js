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

    $('#add_id_build').click(function() {
        return showRelatedObjectPopup(this);
    });

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh');
        populateProductVersion();
    };

    document.getElementById('id_version').onchange = function () {
        $('#id_version').selectpicker('refresh');
    }

    document.getElementById('id_build').onchange = function() {
        $('#id_build').selectpicker('refresh');
    };
}));

// TODO: this entire file is mostly duplicate with testplans/js/mutable.js
function populateProductVersion() {
    let product_id = $('#id_product').val();

    let href = $('#add_id_version')[0].href;
    $('#add_id_version')[0].href = href.slice(0, href.indexOf('&product'));
    $('#add_id_version')[0].href += `&product=${product_id}`;
    $('#id_version').find('option').remove();
    update_version_select_from_product();

    let build_href = $('#add_id_build')[0].href;
    $('#add_id_build')[0].href = build_href.slice(0, build_href.indexOf('&product'));
    $('#add_id_build')[0].href += `&product=${product_id}`;
    update_build_select_from_product();
}
