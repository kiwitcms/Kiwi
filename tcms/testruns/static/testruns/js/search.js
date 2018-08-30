function pre_process_with_product_and_env(data) {
    var plan_cache = {};
    var env_cache = {};

    data.forEach(function(element) {
        // collect info about products
        if (element.plan_id in plan_cache) {
            element['product'] = plan_cache[element.plan_id];
        } else {
            jsonRPC('TestPlan.filter', {pk: element.plan_id}, function(data) {
                element['product'] = data[0].product;
            }, true);
            plan_cache[element.plan_id] = element.product;
        }

        // collect info about env properties
        if (element.env_value in env_cache) {
            element['env_properties'] = env_cache[element.env_value];
        } else if (element.env_value.length === 0) {
            element['env_properties'] = '';
        } else {
            // todo: we can also cache per-property
            var result = '';
            jsonRPC('Env.Value.filter', {pk__in: element.env_value}, function(data){
                data.forEach(function(prop) {
                    result += prop.property + ': ' + prop.value + '<br>';
                });
            }, true);
            element['env_properties'] = result;
            env_cache[element.env_value] = result;
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

            if ($('#id_tag').val()) {
                var tag_list = [];
                $('#id_tag').val().split(',').forEach(function(element) {
                    tag_list.push(element.trim());
                });
                params['tag__name__in'] = tag_list;
            };

            params['stop_date__isnull'] = $('#id_running').is(':checked');

            if ($('#id_env_group').val()) {
                params['plan__env_group'] = $('#id_env_group').val();
            };

            dataTableJsonRPC('TestRun.filter', params, callback, pre_process_with_product_and_env);
        },
        columns: [
            { data: "run_id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/run/'+ data.run_id + '" target="_parent">' + data.summary + '</a>';
                }
            },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.plan_id + '" target="_parent">TP-' + data.plan_id + ': ' + data.plan + '</a>';
                }
            },
            { data: "manager" },
            { data: "default_tester" },
            { data: "product" },
            { data: "product_version"},
            { data: "build"},
            { data: "env_properties" },
            { data: "stop_date"},
        ],
        dom: "t",
        language: {
            zeroRecords: "No records found"
        },
        order: [[ 0, 'asc' ]],
    });

    $('#btn_search').click(function() {
        table.ajax.reload();
        return false; // so we don't actually send the form
    });

    $('#id_product').change(function() {
        var product_id = $(this).val();
        if (product_id) {
            jsonRPC('Version.filter', {product: product_id}, updateVersionSelect);
            jsonRPC('Build.filter', {product: product_id}, updateBuildSelect);
        } else {
            updateVersionSelect([]);
            updateBuildSelect([]);
        }
    });

    $('.bootstrap-switch').bootstrapSwitch();

    $('.selectpicker').selectpicker();
});
