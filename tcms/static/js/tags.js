/*
    Applies tag to the chosen model

    @model - string - model name which accepts tags. There must
        be a 'MM.add_tag' RPC function for this to work!
    @object_id - int - PK of the object that will be tagged
    @tag_input - jQuery object - usually an <input> element which
        provides the value used for tagging
    @to_table - DataTable object - the table which displays the results
*/
function addTag(model, object_id, tag_input, to_table) {
    var tag_name = tag_input.value;

    if (tag_name.length > 0) {
        jsonRPC(model + '.add_tag', [object_id, tag_name], function(data) {
            to_table.row.add({name: tag_name}).draw();
            $(tag_input).val('');
        });
    }
}


/*
    Displays the tags table inside a card and binds all buttons
    and actions for it.

    @model - string - model name which accepts tags. There must
        be a 'MM.add_tag' RPC function for this to work!
    @object_id - int - PK of the object that will be tagged
    @display_filter - dict - passed directly to `Tag.filter` to display
        tags for @object_id
    @perm_remove - bool - if we have permission to remove tags

*/
function tagsCard(model, object_id, display_filter, perm_remove) {
    // load the tags table
    var tags_table = $('#tags').DataTable({
        ajax: function(data, callback, settings) {
            dataTableJsonRPC('Tag.filter', display_filter, callback, function(data, callback) {
                // b/c tags are now annotated with case, run, plan IDs there are duplicate names.
                // Filter them out by only looking at Tag.id uniqueness!
                data = arrayToDict(data)
                callback({'data': Object.values(data)})
            })
        },
        columns: [
            { data: "name" },
            {
                data: null,
                sortable: false,
                render: function (data, type, full, meta) {
                    if (perm_remove) {
                        return '<a href="#tags" class="remove-tag" data-name="' + data.name  + '"><span class="pficon-error-circle-o hidden-print"></span></a>';
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


    // remove tags button
    tags_table.on('draw', function() {
        $('.remove-tag').click(function() {
            var tr = $(this).parents('tr');

            jsonRPC(model + '.remove_tag', [object_id, $(this).data('name')], function(data) {
                tags_table.row($(tr)).remove().draw();
            });
        });
    });

    // add tag button and Enter key
    $('#add-tag').click(function() {
        addTag(model, object_id, $('#id_tags')[0], tags_table);
    });

    $('#id_tags').keyup(function(event) {
        if (event.keyCode === 13) {
            addTag(model, object_id, $('#id_tags')[0], tags_table);
        };
    });

    // tag autocomplete
    $('#id_tags.typeahead').typeahead({
        minLength: 3,
        highlight: true
        }, {
        name: 'tags-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function(element) {
            return element.name;
        },
        source: function(query, processSync, processAsync) {
            jsonRPC('Tag.filter', {name__icontains: query}, function(data) {
                // b/c tags are now annotated with case, run, plan IDs there are duplicate names.
                // Filter them out by only looking at Tag.id uniqueness!
                data = arrayToDict(data)
                return processAsync(Object.values(data));
            });
        }
    });
}
