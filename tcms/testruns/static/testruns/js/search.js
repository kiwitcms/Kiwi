function pre_process_data(data, callback) {
    const runIds = [],
          planIds = []
    data.forEach(function(element) {
        runIds.push(element.id)
        planIds.push(element.plan)
    })

    // get tags for all objects
    const tagsPerRun = {}
    jsonRPC('Tag.filter', {run__in: runIds}, function(tags) {
        tags.forEach(function(element) {
            if (tagsPerRun[element.run] === undefined) {
                tagsPerRun[element.run] = []
            }

            // push only if unique
            if (tagsPerRun[element.run].indexOf(element.name) === -1) {
                tagsPerRun[element.run].push(element.name)
            }
        })

        jsonRPC('Product.filter', {plan__in: planIds}, function(products) {
            products = arrayToDict(products)

            // augment data set with additional info
            data.forEach(function(element) {
                if (element.id in tagsPerRun) {
                    element.tag = tagsPerRun[element.id]
                } else {
                    element.tag = []
                }

                element.product_name = products[element.plan__product].name
            });

            callback({data: data}) // renders everything
        })
    })
}


$(document).ready(function() {
    var table = $("#resultsTable").DataTable({
        pageLength: $('#navbar').data('defaultpagesize'),
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_summary').val()) {
                params['summary__icontains'] = $('#id_summary').val();
            }

            if ($('#id_after_start_date').val()) {
                params['start_date__gte'] = $('#id_after_start_date').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
            }

            if ($('#id_before_start_date').val()) {
                params['start_date__lte'] = $('#id_before_start_date').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
            }

            if ($('#id_after_stop_date').val()) {
                params['stop_date__gte'] = $('#id_after_stop_date').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
            }

            if ($('#id_before_stop_date').val()) {
                params['stop_date__lte'] = $('#id_before_stop_date').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
            }

            if ($('#id_after_planned_start').val()) {
                params['planned_start__gte'] = $('#id_after_planned_start').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
            }

            if ($('#id_before_planned_start').val()) {
                params['planned_start__lte'] = $('#id_before_planned_start').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
            }

            if ($('#id_after_planned_stop').val()) {
                params['planned_stop__gte'] = $('#id_after_planned_stop').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
            }

            if ($('#id_before_planned_stop').val()) {
                params['planned_stop__lte'] = $('#id_before_planned_stop').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
            }

            if ($('#id_plan').val()) {
                params['plan'] = $('#id_plan').val();
            }

            if ($('#id_product').val()) {
                params['plan__product'] = $('#id_product').val();
            };

            if ($('#id_version').val()) {
                params['plan__product_version'] = $('#id_version').val();
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
                    result = '<a href="/runs/'+ data.id + '/">' + escapeHTML(data.summary) + '</a>';
                    if (data.stop_date) {
                        result += '<p class="help-block">' + data.stop_date + '</p>';
                    }
                    return result;
                }
            },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.plan + '/">TP-' + data.plan + ': ' + escapeHTML(data.plan__name) + '</a>';
                }
            },
            { data: "product_name" },
            { data: "plan__product_version__value"},
            { data: "build__name"},
            { data: "manager__username" },
            { data: "default_tester__username" },
            { data: "tag" },
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
    });

    $('#id_version').change(function() {
        update_build_select_from_version(true);
    });

    $('.bootstrap-switch').bootstrapSwitch();

    $('.selectpicker').selectpicker();
});
