$(document).ready(function() {
    var component_cache = {};

    jsonRPC('Component.filter', {}, function(data) {
        for (var key in data) {
            component_cache[data[key].id] = data[key];
        }
    });

    var table = $("#resultsTable").DataTable({
        ajax: function(data, callback, settings) {
            var params = {};

            if ($('#id_summary').val()) {
                params['summary__icontains'] = $('#id_summary').val();
            }

            if ($('#id_before').val()) {
                params['create_date__lte'] = $('#id_before').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59');
            }

            if ($('#id_after').val()) {
                params['create_date__gte'] = $('#id_after').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00');
            }

            if ($('#id_product').val()) {
                params['category__product'] = $('#id_product').val();
            };

            if ($('#id_category').val()) {
                params['category'] = $('#id_category').val();
            };

            if ($('#id_component').val()) {
                params['component'] = $('#id_component').val();
            };

            if ($('#id_priority').val().length > 0) {
                params['priority__in'] = $('#id_priority').val();
            };

            if ($('#id_status').val().length > 0) {
                params['case_status__in'] = $('#id_status').val();
            };

            if ($('#id_author').val()) {
                params['author__username__startswith'] = $('#id_author').val();
            };

            if ($('input[name=is_automated]:checked').val() === 'true') {
                params['is_automated'] = true;
            };

            if ($('input[name=is_automated]:checked').val() === 'false') {
                params['is_automated'] = false;
            };

            updateParamsToSearchTags('#id_tag', params);

            var bug_list = splitByComma($('#id_bugs').val());
            if (bug_list.length > 0) {
                params['case_bug__bug_id__in'] = bug_list;
            };

            dataTableJsonRPC('TestCase.filter', params, callback);
        },
        columns: [
            { data: "case_id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/case/'+ data.case_id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>';
                }
            },
            { data: "author" },
            { data: "default_tester" },
            { data: "is_automated" },
            { data: "case_status"},
            { data: "category"},
            { data: "priority" },
            { data: "create_date"},
            {
                data: "component",
                render: function(components) {
                    str = '';
                    components.forEach(function (pk) {
                        try {
                            str += component_cache[pk].name + ', ';
                        } catch (e) {
                            //TODO: implement better error handling
                            str += '???, '
                        }
                    });
                    // remove trailing coma
                    return str.slice(0, str.lastIndexOf(','));
                }
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
        var updateCategory = function(data) {
            updateSelect(data, '#id_category', 'id', 'name');
        }
        var updateComponent = function(data) {
            updateSelect(data, '#id_component', 'id', 'name');
        }

        var product_id = $(this).val();
        if (product_id) {
            jsonRPC('Category.filter', {product: product_id}, updateCategory);
            jsonRPC('Component.filter', {product: product_id}, updateComponent);
        } else {
            updateCategory([]);
            updateComponent([]);
        }
    });

    $('.selectpicker').selectpicker();
});
