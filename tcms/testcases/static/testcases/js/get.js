const plan_cache = {}


function addComponent(object_id, _input, to_table) {
    var _name = _input.value;

    if (_name.length > 0) {
        jsonRPC('TestCase.add_component', [object_id, _name], function(data) {
            if (data !== undefined) {
                to_table.row.add({name: data.name, id: data.id}).draw();
                $(_input).val('');
            } else {
                $(_input).parents('div.input-group').addClass('has-error');
            }
        });
    }
}


function addTestPlanToTestCase(case_id, plans_table) {
    const plan_name = $('#input-add-plan')[0].value;
    const plan = plan_cache[plan_name];

    jsonRPC('TestPlan.add_case', [plan.id, case_id], function(data) {
        plans_table.row.add({
            id: plan.id,
            name: plan.name,
            author__username: plan.author__username,
            type__name: plan.type__name,
            product__name: plan.product__name
        }).draw();
        $('#input-add-plan').val('');
    });
}


function initAddPlan(case_id, plans_table) {
    // + button
    $('#btn-add-plan').click(function() {
        addTestPlanToTestCase(case_id, plans_table);
    });

    // Enter key
    $('#input-add-plan').keyup(function(event) {
        if (event.keyCode === 13) {
            addTestPlanToTestCase(case_id, plans_table);
        };
    });

    // autocomplete
    $('#input-add-plan.typeahead').typeahead({
        minLength: 1,
        highlight: true
        }, {
        name: 'plans-autocomplete',
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function(element) {
            const display_name = 'TP-' + element.id + ': ' + element.name;
            plan_cache[display_name] = element;
            return display_name;
        },
        source: function(query, processSync, processAsync) {
            // accepts "TP-1234" or "tp-1234" or "1234"
            query = query.toLowerCase().replace('tp-', '');
            if (query === '') {
                return;
            }

            var rpc_query = {pk: query};

            // or arbitrary string
            if (isNaN(query)) {
                if (query.length >=3) {
                    rpc_query = {name__icontains: query};
                } else {
                    return;
                }
            }

            jsonRPC('TestPlan.filter', rpc_query, function(data) {
                return processAsync(data);
            });
        }
    });
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
            dataTableJsonRPC('Component.filter', [{'cases': case_id}], callback);
        },
        columns: [
            { data: "name" },
            {
                data: "id",
                sortable: false,
                render: function (data, type, full, meta) {
                    if (perm_remove_component) {
                        return '<a href="#components" class="remove-component" data-pk="' + data  + '"><span class="pficon-error-circle-o"></span></a>';
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
        // will display up to X results even if more were returned
        limit: 100,
        async: true,
        display: function(element) {
            return element.name;
        },
        source: function(query, processSync, processAsync) {
            jsonRPC('Component.filter', {name__icontains: query, product: product_id}, function(data) {
                data = arrayToDict(data)
                return processAsync(Object.values(data));
            });
        }
    });

    // testplans table
    var plans_table = $('#plans').DataTable({
        ajax: function(data, callback, settings) {
            dataTableJsonRPC('TestPlan.filter', {cases: case_id}, callback);
        },
        columns: [
            { data: "id" },
            {
                data: null,
                render: function (data, type, full, meta) {
                    return '<a href="/plan/'+ data.id + '/">' + escapeHTML(data.name) + '</a>';
                }
            },
            { data: "author__username" },
            { data: "type__name" },
            { data: "product__name" },
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

    // bind add TP to TC widget
    initAddPlan(case_id, plans_table);

    // bugs table
    loadBugs('.bugs', {
        execution__case: case_id,
        is_defect: true
    })

    // executions treeview
    treeViewBind();
});
