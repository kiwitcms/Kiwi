$(document).ready(function() {
    document.getElementById('id_product').onchange = () => {
        $('#id_product').selectpicker('refresh');
        updateTestPlanSelectFromProduct(() => {});
    };

    document.getElementById('id_test_plan').onchange = () => {
        $('#id_test_plan').selectpicker('refresh');

        var updateCallback = function(data) {
            updateSelect(data, '#id_build', 'id', 'name')
        }

        const plan_id = $('#id_test_plan').val();
        if (plan_id) {
            jsonRPC('Build.filter', {version__plans: plan_id, is_active: true}, updateCallback);
        } else {
            updateCallback([]);
        }
    };

    document.getElementById('id_build').onchange = function() {
        $('#id_build').selectpicker('refresh');
    };

    $('#add_id_build').click(function() {
        return showRelatedObjectPopup(this);
    });

    $('.selectpicker').selectpicker();
});
