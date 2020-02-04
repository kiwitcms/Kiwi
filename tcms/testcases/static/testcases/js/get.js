const bug_details_cache = {}


function addComponent(object_id, _input, to_table) {
    var _name = _input.value;

    if (_name.length > 0) {
        jsonRPC('TestCase.add_component', [object_id, _name], function(data) {
            if (data !== undefined) {
                to_table.row.add({name: _name}).draw();
                $(_input).val('');
            } else {
                $(_input).parents('div.input-group').addClass('has-error');
            }
        });
    }
}


$(document).ready(function() {
    var case_id = $('#test_case_pk').data('pk');
    var product_id = $('#product_pk').data('pk');
    var perm_remove_tag = $('#test_case_pk').data('perm-remove-tag') === 'True';
    var perm_remove_component = $('#test_case_pk').data('perm-remove-component') === 'True';
    var perm_remove_plan = $('#test_case_pk').data('perm-remove-plan') === 'True';
    var perm_remove_bug = $('#test_case_pk').data('perm-remove-bug') === 'True';

    // bind everything in tags table
    tagsCard('TestCase', case_id, {case: case_id}, perm_remove_tag);

    // components table
    var components_table = $('#components').DataTable({
        ajax: function(data, callback, settings) {
            dataTableJsonRPC('TestCase.get_components', [case_id], callback);
        },
        columns: [
            { data: "name" },
            {
                data: null,
                sortable: false,
                render: function (data, type, full, meta) {
                    if (perm_remove_component) {
                        return '<a href="#components" class="remove-component" data-pk="' + data.id  + '"><span class="pficon-error-circle-o"></span></a>';
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

    // remove component button
    components_table.on('draw', function() {
        $('.remove-component').click(function() {
            var tr = $(this).parents('tr');

            jsonRPC('TestCase.remove_component', [case_id, $(this).data('pk')], function(data) {
                components_table.row($(tr)).remove().draw();
            });
        });
    });

    // add component button and Enter key
    $('#add-component').click(function() {
        addComponent(case_id, $('#id_components')[0], components_table);
    });

    $('#id_components').keyup(function(event) {
        if (event.keyCode === 13) {
            addComponent(case_id, $('#id_components')[0], components_table);
        };
    });

    // components autocomplete
    $('#id_components.typeahead').typeahead({
        minLength: 3,
        highlight: true
        }, {
        name: 'components-autocomplete',
        source: function(query, processSync, processAsync) {
            jsonRPC('Component.filter', {name__startswith: query, product: product_id}, function(data) {
                var processedData = [];
                data.forEach(function(element) {
                    processedData.push(element.name);
                });
                return processAsync(processedData);
            });
        }
    });

    // testplans table
    var plans_table = $('#plans').DataTable({
        ajax: function(data, callback, settings) {
            dataTableJsonRPC('TestPlan.filter', {case: case_id}, callback);
        },
        columns: [
            { data: "id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.id + '/">' + escapeHTML(data.name) + '</a>';
                }
            },
            { data: "author" },
            { data: "type"},
            { data: "product" },
            {
                data: null,
                sortable: false,
                render: function (data, type, full, meta) {
                    if (perm_remove_plan) {
                        return '<a href="#plans" class="remove-plan" data-pk="' + data.id  + '"><span class="pficon-error-circle-o"></span></a>';
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

    // remove plan button
    plans_table.on('draw', function() {
        $('.remove-plan').click(function() {
            var tr = $(this).parents('tr');

            jsonRPC('TestPlan.remove_case', [$(this).data('pk'), case_id], function(data) {
                plans_table.row($(tr)).remove().draw();
            });
        });
    });

    // bugs table
    $('#bugs').DataTable({
        ajax: function(data, callback, settings) {
            dataTableJsonRPC('TestExecution.get_links',
                             {execution__case: case_id,
                              is_defect: true}, callback);
        },
        columns: [
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="' + data.url + '" class="bug-url">' + data.url + '</a>';
                }
            },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="#bugs" data-toggle="popover" data-html="true" ' +
                                'data-content="undefined" data-trigger="focus" data-placement="top">' +
                                '<span class="fa fa-info-circle"></span>' +
                           '</a>';
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

    $('#bugs').on('draw.dt', function () {
        $('#bugs').find('[data-toggle=popover]')
        .popovers()
        .on('show.bs.popover', function(element) {
            fetchBugDetails($(element.target).parents('tr').find('.bug-url')[0],
                            element.target,
                            bug_details_cache);
        });
    });

    $('[data-toggle=popover]')
        .popovers()
        .on('show.bs.popover', function(element) {
            fetchBugDetails($(element.target).parents('.list-view-pf-body').find('.bug-url')[0],
                            element.target,
                            bug_details_cache);
    });

    // executions treeview
    treeViewBind();
});


function assignPopoverData(source, popover, data) {
    source.title = data.title;
    $(popover).attr('data-original-title', data.title);
    $(popover).attr('data-content', data.description);
}


function fetchBugDetails(source, popover, cache) {
    if (source.href in cache) {
        assignPopoverData(source, popover, cache[source.href]);
        return;
    }

    jsonRPC('Bug.details', [source.href], function(data) {
        cache[source.href] = data;
        assignPopoverData(source, popover, data);
    }, true);
}
