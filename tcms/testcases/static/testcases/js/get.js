function addTag(module, object_id, tag_input, to_table) {
    var tag_name = tag_input.value;

    if (tag_name.length > 0) {
        jsonRPC(module + '.add_tag', [object_id, tag_name], function(data) {
            to_table.row.add({name: tag_name}).draw();
            $(tag_input).val('');
        });
    }
}


$(document).ready(function() {
    var case_id = $('#test_case_pk').data('pk');
    var perm_remove_tag = $('#test_case_pk').data('perm-remove-tag') === 'True';

    var tags_table = $('#tags').DataTable({
        ajax: function(data, callback, settings) {
            var params = {};
            dataTableJsonRPC('Tag.filter', {case: case_id}, callback);
        },
        columns: [
            { data: "name" },
            {
                data: null,
                sortable: false,
                render: function (data, type, full, meta) {
                    if (perm_remove_tag) {
                        return '<a href="#tags" class="remove-tag" data-name="' + data.name  + '"><span class="pficon-error-circle-o"></span></a>';
                    }
                    return '';
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

    // remove button
    tags_table.on('draw', function() {
        $('.remove-tag').click(function() {
            var tr = $(this).parents('tr');

            jsonRPC('TestCase.remove_tag', [case_id, $(this).data('name')], function(data) {
                tags_table.row($(tr)).remove().draw();
            });
        });
    });

    // add button and Enter key
    $('#add-tag').click(function() {
        addTag('TestCase', case_id, $('#id_tags')[0], tags_table);
    });

    $('#id_tags').keyup(function(event) {
        if (event.keyCode === 13) {
            addTag('TestCase', case_id, $('#id_tags')[0], tags_table);
        };
    });

    // autocomplete
    $('.typeahead').typeahead({
        minLength: 3,
        highlight: true
        }, {
        name: 'tags-autocomplete',
        source: function(query, processSync, processAsync) {
            jsonRPC('Tag.filter', {'name__startswith': query}, function(data) {
                var processedData = [];
                data.forEach(function(element) {
                    processedData.push(element.name);
                });
                return processAsync(processedData);
            });
        }
    });
});
