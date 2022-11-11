const whenReady = {
    'page-testcases-get': () => {
        const planCache = {}

        function addComponent (objectId, _input, toTable) {
            const _name = _input.value

            if (_name.length > 0) {
                jsonRPC('TestCase.add_component', [objectId, _name], function (data) {
                    if (data !== undefined) {
                        toTable.row.add({ name: data.name, id: data.id }).draw()
                        $(_input).val('')
                    } else {
                        $(_input).parents('div.input-group').addClass('has-error')
                    }
                })
            }
        }

        function addTestPlanToTestCase (caseId, plansTable) {
            const planName = $('#input-add-plan')[0].value
            const plan = planCache[planName]

            jsonRPC('TestPlan.add_case', [plan.id, caseId], function (data) {
                plansTable.row.add({
                    id: plan.id,
                    name: plan.name,
                    author__username: plan.author__username,
                    type__name: plan.type__name,
                    product__name: plan.product__name
                }).draw()
                $('#input-add-plan').val('')
            })
        }

        function initAddPlan (caseId, plansTable) {
            // + button
            $('#btn-add-plan').click(function () {
                addTestPlanToTestCase(caseId, plansTable)
            })

            // Enter key
            $('#input-add-plan').keyup(function (event) {
                if (event.keyCode === 13) {
                    addTestPlanToTestCase(caseId, plansTable)
                };
            })

            // autocomplete
            $('#input-add-plan.typeahead').typeahead({
                minLength: 1,
                highlight: true
            }, {
                name: 'plans-autocomplete',
                // will display up to X results even if more were returned
                limit: 100,
                async: true,
                display: function (element) {
                    const displayName = 'TP-' + element.id + ': ' + element.name
                    planCache[displayName] = element
                    return displayName
                },
                source: function (query, processSync, processAsync) {
                    // accepts "TP-1234" or "tp-1234" or "1234"
                    query = query.toLowerCase().replace('tp-', '')
                    if (query === '') {
                        return
                    }

                    let rpcQuery = { pk: query }

                    // or arbitrary string
                    if (isNaN(query)) {
                        if (query.length >= 3) {
                            rpcQuery = { name__icontains: query }
                        } else {
                            return
                        }
                    }

                    jsonRPC('TestPlan.filter', rpcQuery, function (data) {
                        return processAsync(data)
                    })
                }
            })
        }

        const caseId = $('#test_case_pk').data('pk')
        const productId = $('#product_pk').data('pk')
        const permRemoveTag = $('#test_case_pk').data('perm-remove-tag') === 'True'
        const permRemoveComponent = $('#test_case_pk').data('perm-remove-component') === 'True'
        const permRemovePlan = $('#test_case_pk').data('perm-remove-plan') === 'True'

        propertiesCard(caseId, 'case', 'TestCase.properties', 'TestCase.add_property', 'TestCase.remove_property')

        // bind everything in tags table
        tagsCard('TestCase', caseId, { case: caseId }, permRemoveTag)

        // components table
        const componentsTable = $('#components').DataTable({
            ajax: function (data, callback, settings) {
                dataTableJsonRPC('Component.filter', [{ cases: caseId }], callback)
            },
            columns: [
                { data: 'name' },
                {
                    data: 'id',
                    sortable: false,
                    render: function (data, type, full, meta) {
                        if (permRemoveComponent) {
                            return '<a href="#components" class="remove-component" data-pk="' + data + '"><span class="pficon-error-circle-o"></span></a>'
                        }
                        return ''
                    }
                }
            ],
            dom: 't',
            language: {
                loadingRecords: '<div class="spinner spinner-lg"></div>',
                processing: '<div class="spinner spinner-lg"></div>',
                zeroRecords: 'No records found'
            },
            order: [[0, 'asc']]
        })

        // remove component button
        componentsTable.on('draw', function () {
            $('.remove-component').click(function () {
                const tr = $(this).parents('tr')

                jsonRPC('TestCase.remove_component', [caseId, $(this).data('pk')], function (data) {
                    componentsTable.row($(tr)).remove().draw()
                })
            })
        })

        // add component button and Enter key
        $('#add-component').click(function () {
            addComponent(caseId, $('#id_components')[0], componentsTable)
        })

        $('#id_components').keyup(function (event) {
            if (event.keyCode === 13) {
                addComponent(caseId, $('#id_components')[0], componentsTable)
            };
        })

        // components autocomplete
        $('#id_components.typeahead').typeahead({
            minLength: 3,
            highlight: true
        }, {
            name: 'components-autocomplete',
            // will display up to X results even if more were returned
            limit: 100,
            async: true,
            display: function (element) {
                return element.name
            },
            source: function (query, processSync, processAsync) {
                jsonRPC('Component.filter', { name__icontains: query, product: productId }, function (data) {
                    data = arrayToDict(data)
                    return processAsync(Object.values(data))
                })
            }
        })

        // testplans table
        const plansTable = $('#plans').DataTable({
            ajax: function (data, callback, settings) {
                dataTableJsonRPC('TestPlan.filter', { cases: caseId }, callback)
            },
            columns: [
                { data: 'id' },
                {
                    data: null,
                    render: function (data, type, full, meta) {
                        return '<a href="/plan/' + data.id + '/">' + escapeHTML(data.name) + '</a>'
                    }
                },
                { data: 'author__username' },
                { data: 'type__name' },
                { data: 'product__name' },
                {
                    data: null,
                    sortable: false,
                    render: function (data, type, full, meta) {
                        if (permRemovePlan) {
                            return '<a href="#plans" class="remove-plan" data-pk="' + data.id + '"><span class="pficon-error-circle-o"></span></a>'
                        }
                        return ''
                    }
                }
            ],
            dom: 't',
            language: {
                loadingRecords: '<div class="spinner spinner-lg"></div>',
                processing: '<div class="spinner spinner-lg"></div>',
                zeroRecords: 'No records found'
            },
            order: [[0, 'asc']]
        })

        // remove plan button
        plansTable.on('draw', function () {
            $('.remove-plan').click(function () {
                const tr = $(this).parents('tr')

                jsonRPC('TestPlan.remove_case', [$(this).data('pk'), caseId], function (data) {
                    plansTable.row($(tr)).remove().draw()
                })
            })
        })

        // bind add TP to TC widget
        initAddPlan(caseId, plansTable)

        // bugs table
        loadBugs('.bugs', {
            execution__case: caseId,
            is_defect: true
        })

        // executions treeview
        treeViewBind()
    },

    'page-testcases-mutable': () => {
        $('#text_templates').change(function () {
            markdownEditor.codemirror.setValue($(this).val())
        })

        if ($('#id_category').find('option').length === 0) {
            populateCategory()
        }

        $('#add_id_product').click(function () {
            return showRelatedObjectPopup(this)
        })

        $('#add_id_category').click(function () {
            return showRelatedObjectPopup(this)
        })

        document.getElementById('id_product').onchange = function () {
            $('#id_product').selectpicker('refresh')
            populateCategory()
        }

        document.getElementById('id_category').onchange = function () {
            $('#id_category').selectpicker('refresh')
        }
    },
    'page-testcases-search': () => {
        function preProcessData (data, callback) {
            const caseIds = []
            data.forEach(function (element) {
                caseIds.push(element.id)
            })

            // get tags for all objects
            const tagsPerCase = {}
            jsonRPC('Tag.filter', { case__in: caseIds }, function (tags) {
                tags.forEach(function (element) {
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
                jsonRPC('Component.filter', { cases__in: caseIds }, function (components) {
                    components.forEach(function (element) {
                        if (componentsPerCase[element.cases] === undefined) {
                            componentsPerCase[element.cases] = []
                        }

                        // push only if unique
                        if (componentsPerCase[element.cases].indexOf(element.name) === -1) {
                            componentsPerCase[element.cases].push(element.name)
                        }
                    })

                    // augment data set with additional info
                    data.forEach(function (element) {
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
                    })

                    callback({ data }) // renders everything
                })
            })
        }

        const table = $('#resultsTable').DataTable({
            pageLength: $('#navbar').data('defaultpagesize'),
            ajax: function (data, callback, settings) {
                const params = {}

                if ($('#id_summary').val()) {
                    params.summary__icontains = $('#id_summary').val()
                }

                if ($('#id_before').val()) {
                    params.create_date__lte = $('#id_before').data('DateTimePicker').date().format('YYYY-MM-DD 23:59:59')
                }

                if ($('#id_after').val()) {
                    params.create_date__gte = $('#id_after').data('DateTimePicker').date().format('YYYY-MM-DD 00:00:00')
                }

                if ($('#id_product').val()) {
                    params.category__product = $('#id_product').val()
                };

                if ($('#id_category').val()) {
                    params.category = $('#id_category').val()
                };

                if ($('#id_component').val()) {
                    params.component = $('#id_component').val()
                };

                if ($('#id_priority').val().length > 0) {
                    params.priority__in = $('#id_priority').val()
                };

                if ($('#id_status').val().length > 0) {
                    params.case_status__in = $('#id_status').val()
                };

                if ($('#id_author').val()) {
                    params.author__username__startswith = $('#id_author').val()
                };

                if ($('#id_run').val()) {
                    params.executions__run__in = $('#id_run').val()
                };

                const testPlanIds = $('#id_test_plan').val()
                if (testPlanIds.length) {
                    params.plan__in = testPlanIds
                }

                if ($('input[name=is_automated]:checked').val() === 'true') {
                    params.is_automated = true
                };

                if ($('input[name=is_automated]:checked').val() === 'false') {
                    params.is_automated = false
                };

                const text = $('#id_text').val()
                if (text) {
                    params.text__icontains = text
                };

                updateParamsToSearchTags('#id_tag', params)

                dataTableJsonRPC('TestCase.filter', params, callback, preProcessData)
            },
            select: {
                className: 'success',
                style: 'multi',
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
                        return `<input type="checkbox" value="${data.id}" name="row-check">`
                    }
                },
                { data: 'id' },
                {
                    data: null,
                    render: function (data, type, full, meta) {
                        return '<a href="/case/' + data.id + '/" target="_parent">' + escapeHTML(data.summary) + '</a>'
                    }
                },
                { data: 'create_date' },
                { data: 'category__name' },
                { data: 'component_names' },
                { data: 'priority__value' },
                { data: 'case_status__name' },
                { data: 'is_automated' },
                { data: 'author__username' },
                { data: 'tag_names' }
            ],
            dom: 't',
            language: {
                loadingRecords: '<div class="spinner spinner-lg"></div>',
                processing: '<div class="spinner spinner-lg"></div>',
                zeroRecords: 'No records found'
            },
            order: [[1, 'asc']]
        })

        hookIntoPagination('#resultsTable', table)

        const selectAllButton = $('#check-all')

        selectAllButton.click(function () {
            const rowCheckboxInputButton = $("input:checkbox[name='row-check']")
            const isChecked = selectAllButton.prop('checked')
            rowCheckboxInputButton.prop('checked', isChecked)
            isChecked ? table.rows().select() : table.rows().deselect()
        })

        table.on('select', function (e, dt, type, indexes) {
            if (type === 'row') {
                const totalRows = $("input:checkbox[name='row-check']").length
                const selectedRows = $("input:checkbox[name='row-check']:checked").length
                selectAllButton.prop('checked', totalRows === selectedRows)
            }
        })

        table.on('deselect', function (e, dt, type, indexes) {
            if (type === 'row') {
                selectAllButton.prop('checked', false)
            }
        })

        $('#select-btn').click(function (event) {
            event.preventDefault()
            const testCaseIDs = []

            table.rows({ selected: true }).data().each(function (selected) {
                testCaseIDs.push(selected.id)
            })

            if (testCaseIDs && window.opener) {
                window.opener.addTestCases(testCaseIDs, window)
            }

            return false
        })

        $('#btn_search').click(function () {
            table.ajax.reload()
            return false // so we don't actually send the form
        })

        $('#id_product').change(function () {
            updateComponentSelectFromProduct()
            updateCategorySelectFromProduct()
            updateTestPlanSelectFromProduct()
        })

        $('#id_test_plan').change(function () {
            $(this).parents('.bootstrap-select').toggleClass('open')
        })
    }
}

$(() => {
    const pageId = $('body').attr('id')
    const readyFunc = whenReady[pageId]
    if (readyFunc) {
        readyFunc()
    }

    $('.bootstrap-switch').bootstrapSwitch()
    $('.selectpicker').selectpicker()
})
