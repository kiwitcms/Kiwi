function addTag(module, object_id, tag_input, to_table) {
    var tag_name = tag_input.value;

    if (tag_name.length > 0) {
        jsonRPC(module + '.add_tag', [object_id, tag_name], function(data) {
            to_table.row.add({name: tag_name}).draw();
            $(tag_input).val('');
        });
    }
}


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
    var bug_systems_cache = {}
    jsonRPC('BugSystem.filter', {}, function(data) {
        data.forEach(function(element) {
            bug_systems_cache[element.id] = element
        });
    });

    var case_id = $('#test_case_pk').data('pk');
    var product_id = $('#product_pk').data('pk');
    var perm_remove_tag = $('#test_case_pk').data('perm-remove-tag') === 'True';
    var perm_remove_component = $('#test_case_pk').data('perm-remove-component') === 'True';
    var perm_remove_plan = $('#test_case_pk').data('perm-remove-plan') === 'True';
    var perm_remove_bug = $('#test_case_pk').data('perm-remove-bug') === 'True';


    // tags table
    var tags_table = $('#tags').DataTable({
        ajax: function(data, callback, settings) {
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

    // remove tags button
    tags_table.on('draw', function() {
        $('.remove-tag').click(function() {
            var tr = $(this).parents('tr');

            jsonRPC('TestCase.remove_tag', [case_id, $(this).data('name')], function(data) {
                tags_table.row($(tr)).remove().draw();
            });
        });
    });

    // add tag button and Enter key
    $('#add-tag').click(function() {
        addTag('TestCase', case_id, $('#id_tags')[0], tags_table);
    });

    $('#id_tags').keyup(function(event) {
        if (event.keyCode === 13) {
            addTag('TestCase', case_id, $('#id_tags')[0], tags_table);
        };
    });

    // tag autocomplete
    $('#id_tags.typeahead').typeahead({
        minLength: 3,
        highlight: true
        }, {
        name: 'tags-autocomplete',
        source: function(query, processSync, processAsync) {
            jsonRPC('Tag.filter', {name__startswith: query}, function(data) {
                var processedData = [];
                data.forEach(function(element) {
                    processedData.push(element.name);
                });
                return processAsync(processedData);
            });
        }
    });

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
            { data: "plan_id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.plan_id + '/">' + escapeHTML(data.name) + '</a>';
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
                        return '<a href="#plans" class="remove-plan" data-pk="' + data.plan_id  + '"><span class="pficon-error-circle-o"></span></a>';
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
    var bugs_table = $('#bugs').DataTable({
        ajax: function(data, callback, settings) {
            dataTableJsonRPC('Bug.filter', {case: case_id}, callback);
        },
        columns: [
            {
                data: null,
                render: function (data, type, full, meta) {
                    var url = bug_systems_cache[data.bug_system_id].url_reg_exp.replace('%s', data.bug_id).replace('%d', data.bug_id);
                    var name = bug_systems_cache[data.bug_system_id].name + ' #' + data.bug_id;
                    return '<a href="' + url + '">' + name + '</a>';
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


    // executions treeview
    // collapse all child rows
    $('.tree-list-view-pf').find(".list-group-item-container").addClass('hidden');

    // click the list-view heading then expand a row
    $('.list-group-item-header').click(function (event) {
      if(!$(event.target).is('button, a, input, .fa-ellipsis-v')) {
        var $this = $(this);
        $this.find('.fa-angle-right').toggleClass('fa-angle-down');
        var $itemContainer = $this.siblings('.list-group-item-container');
        if ($itemContainer.children().length) {
          $itemContainer.toggleClass('hidden');
        }
      }
    });

});
