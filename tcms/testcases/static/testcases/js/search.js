function pre_process_data(data, callback) {
    const caseIds = []
    data.forEach(function(element) {
        caseIds.push(element.id)
    })

    // get tags for all objects
    const tagsPerCase = {}
    jsonRPC('Tag.filter', {case__in: caseIds}, function(tags) {
        tags.forEach(function(element) {
            if (tagsPerCase[element.case] === undefined) {
                tagsPerCase[element.case] = []
            }

            // push only if unique
            if (tagsPerCase[element.case].indexOf(element.name) === -1) {
                tagsPerCase[element.case].push(element.name)
            }
        })

        // get components for all objects
        const componentsPerCase = {}
        jsonRPC('Component.filter', {cases__in: caseIds}, function(components) {
            components.forEach(function(element) {
                if (componentsPerCase[element.cases] === undefined) {
                    componentsPerCase[element.cases] = []
                }

                // push only if unique
                if (componentsPerCase[element.cases].indexOf(element.name) === -1) {
                    componentsPerCase[element.cases].push(element.name)
                }
            })

            // augment data set with additional info
            data.forEach(function(element) {
                if (element.id in tagsPerCase) {
                    element.tag_names = tagsPerCase[element.id]
                } else {
                    element.tag_names = []
                }

                if (element.id in componentsPerCase) {
                    element.component_names = componentsPerCase[element.id]
                } else {
                    element.component_names = []
                }
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
            { data: "category__name"},
            { data: "component_names" },
            { data: "priority__value" },
            { data: "case_status__name"},
            { data: "is_automated" },
            { data: "author__username" },
            { data: "tag_names" },
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
            window.opener.addTestCases(testCaseIDs, window);
        }

        return false;
    });

    $('#btn_search').click(function() {
        table.ajax.reload();
        return false; // so we don't actually send the form
    });

    $('#id_product').change(function() {
        update_component_select_from_product()
        update_category_select_from_product()
    });

    $('.selectpicker').selectpicker();
});
