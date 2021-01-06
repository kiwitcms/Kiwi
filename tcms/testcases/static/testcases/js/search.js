function pre_process_data(data) {
    var component_cache = {};
    var tags_cache = {};

    data.forEach(function(element) {
        addResourceToData(element, 'component', 'Component.filter', component_cache);
        addResourceToData(element, 'tag', 'Tag.filter', tags_cache);
    });
}


$(document).ready(function() {
    var table = $("#resultsTable").DataTable({
        pageLength: $('#navbar').data('defaultpagesize'),
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

            // todo: see BaseCaseSearchForm
            const text = $('#id_text').val();
            if (text) {
                params['text__icontains'] = text;
            };

            updateParamsToSearchTags('#id_tag', params);

            dataTableJsonRPC('TestCase.filter', params, callback, pre_process_data);
        },
        select: {
            className: 'success',
            style:    'multi',
            selector: 'td > input'
        },
        columns: [
            {
                data: null,
                sortable: false,
                orderable: false,
                target: 1,
                className: 'js-select-checkbox',
                render: function (data, type, full, meta) {
                    return `<input type="checkbox" value="${data.id}" name="row-check">`;
                }
            },
            { data: "id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/case/'+ data.id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>';
                }
            },
            { data: "create_date"},
            { data: "category"},
            {
                data: "component",
                render: renderFromCache,
            },
            { data: "priority" },
            { data: "case_status"},
            { data: "is_automated" },
            { data: "author" },
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
        order: [[ 1, 'asc' ]],
    });

    hookIntoPagination('#resultsTable', table);

    const selectAllButton = $("#check-all")

    selectAllButton.click(function () {
        const rowCheckboxInputButton = $("input:checkbox[name='row-check']")
        const isChecked = selectAllButton.prop("checked")
        rowCheckboxInputButton.prop("checked", isChecked)
        isChecked ? table.rows().select() : table.rows().deselect()
    });

    table.on('select', function (e, dt, type, indexes) {
        if (type === 'row') {
            const totalRows = $("input:checkbox[name='row-check']").length;
            const selectedRows = $("input:checkbox[name='row-check']:checked").length;
            selectAllButton.prop("checked", totalRows === selectedRows)
        }
    });

    table.on('deselect', function (e, dt, type, indexes) {
        if (type === 'row') {
            selectAllButton.prop("checked", false)
        } 
    });

    $('#select-btn').click(function(event){
        event.preventDefault();
        let testCaseIDs = [];

        table.rows({ selected:true }).data().each(function(selected){
            testCaseIDs.push(selected.id);
        });

        if (testCaseIDs && window.opener) {
            window.opener.$('#popup-selection').val(testCaseIDs);
            window.close();
        }

        return false;
    });

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
