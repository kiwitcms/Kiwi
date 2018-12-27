$(document).ready(function() {
    var case_id = $('#test_case_pk').data('pk');

    var table = $('#tags').DataTable({
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
                    return '<a href="#" class="remove-tag" data-param="' + data.id  + '"><span class="pficon-error-circle-o"></span></a>';
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

    table.on('draw', function() {
        $('.remove-tag').click(function() {
            jsonRPC('TestCase.remove_tag', [case_id, $(this).data('param')], console.log)
        });
    });


    setAddTagAutocomplete();

//    $('#js-add-tag').bind('click', function() {
//        addTag($('#tag')[0]);
//    });

});
