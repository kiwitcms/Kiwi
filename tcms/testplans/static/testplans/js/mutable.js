$(document).ready((function () {
    populateProductVersion();

    $('#id_product').change(populateProductVersion);

    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this);
    });

    $('#add_id_version').click(function () {
        return showRelatedObjectPopup(this);
    });
}));

function populateProductVersion() {
    let href = $('#add_id_version')[0].href;
    $('#add_id_version')[0].href = href.slice(0, href.indexOf('&product'));
    $('#add_id_version')[0].href += `&product=${$('#id_product').val()}`;

    $('#id_version').find('option').remove();

    update_version_select_from_product();
}
