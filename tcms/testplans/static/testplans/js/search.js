$(document).ready(function() {
    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_name').val()) {
                params['name__icontains'] = $('#id_name').val();
            }

            if ($('#id_before').val()) {
                params['create_date__lte'] = $('#id_before').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
            }

            if ($('#id_after').val()) {
                params['create_date__gte'] = $('#id_after').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
            }

            if ($('#id_product').val()) {
                params['product'] = $('#id_product').val();
            };

            if ($('#id_version').val()) {
                params['product_version'] = $('#id_version').val();
            };

            if ($('#id_type').val()) {
                params['type'] = $('#id_type').val();
            };

            if ($('#id_author').val()) {
                params['author__username__startswith'] = $('#id_author').val();
            };

            if ($('#id_owner').val()) {
                params['owner__username__startswith'] = $('#id_owner').val();
            };

            if ($('#id_default_tester').val()) {
                params['case__default_tester__username__startswith'] = $('#id_default_tester').val();
            };

            updateParamsToSearchTags('#id_tag', params);

            params['is_active'] = $('#id_active').is(':checked');

            dataTableJsonRPC('TestPlan.filter', params, callback);
        },
        columns: [
            { data: "plan_id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.plan_id + '/">' + escapeHTML(data.name) + '</a>';
                }
            },
            { data: "create_date" },
            { data: "author" },
            { data: "owner" },
            { data: "product" },
            { data: "type"}
        ],
        dom: "t",
        language: {
            zeroRecords: "No records found"
        },
        order: [[ 0, 'asc' ]],
    });

    hookIntoPagination('#resultsTable', table);

    $('#btn_search').click(function() {
        table.ajax.reload();
        return false; // so we don't actually send the form
    });

    $('#id_product').change(update_version_select_from_product);

    $('.bootstrap-switch').bootstrapSwitch();

    $('.selectpicker').selectpicker();
});
