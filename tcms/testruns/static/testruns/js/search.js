function pre_process_data(data) {
    var product_cache = {};
    var tags_cache = {};

    data.forEach(function(element) {
        // collect info about products
        addResourceToData(element, 'tag', 'Tag.filter', tags_cache);

        if (element.plan_id in product_cache) {
            element['product'] = product_cache[element.plan_id];
        } else {
            jsonRPC('TestPlan.filter', {pk: element.plan_id}, function(data) {
                element['product'] = data[0].product;
            }, true);
            product_cache[element.plan_id] = element.product;
        }
    });
}


$(document).ready(function() {
    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_summary').val()) {
                params['summary__icontains'] = $('#id_summary').val();
            }

            if ($('#id_plan').val()) {
                params['plan'] = $('#id_plan').val();
            }

            if ($('#id_product').val()) {
                params['plan__product'] = $('#id_product').val();
            };

            if ($('#id_version').val()) {
                params['product_version'] = $('#id_version').val();
            };

            if ($('#id_build').val()) {
                params['build'] = $('#id_build').val();
            };

            if ($('#id_manager').val()) {
                params['manager__username__startswith'] = $('#id_manager').val();
            };

            if ($('#id_default_tester').val()) {
                params['default_tester__username__startswith'] = $('#id_default_tester').val();
            };

            updateParamsToSearchTags('#id_tag', params);

            params['stop_date__isnull'] = $('#id_running').is(':checked');

            dataTableJsonRPC('TestRun.filter', params, callback, pre_process_data);
        },
        columns: [
            { data: "id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    result = '<a href="/runs/'+ data.id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>';
                    if (data.stop_date) {
                        result += '<p class="help-block">' + data.stop_date + '</p>';
                    }
                    return result;
                }
            },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.plan_id + '/" target="_parent">TP-' + data.plan_id + ': ' + escapeHTML(data.plan) + '</a>';
                }
            },
            { data: "product" },
            { data: "product_version"},
            { data: "build"},

            { data: "manager" },
            { data: "default_tester" },
            {
                data: "tag",
                render: renderFromCache,
            },
        ],
        dom: "t",
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: "No records found"
        },
        order: [[ 0, 'asc' ]],
    });

    hookIntoPagination('#resultsTable', table);

    $('#btn_search').click(function() {
        table.ajax.reload();
        return false; // so we don't actually send the form
    });

    $('#id_product').change(function() {
        update_version_select_from_product();
        update_build_select_from_product(true);
    });

    $('.bootstrap-switch').bootstrapSwitch();

    $('.selectpicker').selectpicker();
});
