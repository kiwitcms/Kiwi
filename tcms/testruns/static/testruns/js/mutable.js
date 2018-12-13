$(document).ready(function() {
    $('#add_id_build').click(function() {
        return showRelatedObjectPopup(this);
    });

    $('.selectpicker').selectpicker();

    document.getElementById('id_build').onchange = function() {
        $('#id_build').selectpicker('refresh');
    };
});
