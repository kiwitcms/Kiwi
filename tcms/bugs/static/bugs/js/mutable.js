$(document).ready((function () {

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
        populateVersion();
    };

    document.getElementById('id_version').onchange = function () {
        $('#id_version').selectpicker('refresh');
        populateBuild();
    }

    document.getElementById('id_build').onchange = function() {
        $('#id_build').selectpicker('refresh');
    };

    // initialize at the end b/c we rely on .change() event to initialize builds
    if ($('#id_version').find('option').length === 0) {
        populateVersion();
    }
}));

// TODO: this entire file is mostly duplicate with testplans/js/mutable.js
function populateVersion() {
    let product_id = $('#id_product').val();

    let href = $('#add_id_version')[0].href;
    $('#add_id_version')[0].href = href.slice(0, href.indexOf('&product'));
    $('#add_id_version')[0].href += `&product=${product_id}`;
    $('#id_version').find('option').remove();
    update_version_select_from_product();
}

function populateBuild() {
    let product_id = $('#id_version').val();

    let href = $('#add_id_build')[0].href;
    $('#add_id_build')[0].href = href.slice(0, href.indexOf('&version'));
    $('#add_id_build')[0].href += `&version=${product_id}`;
    update_build_select_from_version();
}
