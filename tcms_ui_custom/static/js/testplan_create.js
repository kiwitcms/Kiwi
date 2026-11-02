document.addEventListener("DOMContentLoaded", function() {
    if (!window.jQuery) return;
    const $ = window.jQuery;

    const form = document.getElementById('testPlanForm');
    const apiModulesUrl = form.getAttribute('data-url-modules');
    const apiCasesUrl = form.getAttribute('data-url-cases');
    const apiVersionsUrl = form.getAttribute('data-url-versions');
    const selectedProductId = form.getAttribute('data-selected-product');

    // 1. Init Select2
    $('#id_strategies').select2({ placeholder: "Select Test Strategies...", width: '100%' });
    $('#id_resources').select2({ placeholder: "Select Team Members...", width: '100%' });
    $('#id_modules').select2({ placeholder: "Select Modules...", width: '100%' });

    // 2. Define the change handlers FIRST
    $('#id_product').change(function() {
        const productId = $(this).val();

        // Clear and disable modules
        $('#id_modules').val(null).trigger('change');
        $('#id_modules').empty().prop('disabled', true);

        // Clear versions
        $('#id_product_version').empty().append('<option value="">Select Version...</option>');

        $('#in-scope-container').html('<p class="text-light text-center">Select Modules to load cases.</p>');
        $('#out-scope-container').html('<p class="text-light text-center">Excluded test cases will appear here.</p>');

        if (productId) {
            // Fetch Modules
            $.ajax({
                url: apiModulesUrl,
                data: { product_id: productId },
                success: function(data) {
                    if (data.modules.length > 0) {
                        data.modules.forEach(function(mod) {
                            $('#id_modules').append(new Option(mod.name, mod.id, false, false));
                        });
                        $('#id_modules').prop('disabled', false);
                    }
                }
            });

            // Fetch Versions
            $.ajax({
                url: apiVersionsUrl,
                data: { product_id: productId },
                success: function(data) {
                    if (data.versions.length > 0) {
                        data.versions.forEach(function(v) {
                            $('#id_product_version').append(new Option(v.value, v.id, false, false));
                        });
                    } else {
                        $('#id_product_version').append(new Option('No versions available', '', false, false));
                    }
                }
            });
        }
    });

    $('#id_modules').change(function() {
        const moduleIds = $(this).val();

        $('#in-scope-container').html('<p class="text-light text-center">Loading test cases...</p>');
        $('#out-scope-container').html('<p class="text-light text-center">Excluded test cases will appear here.</p>');

        if (!moduleIds || moduleIds.length === 0) return;

        $.ajax({
            url: apiCasesUrl,
            data: { components: moduleIds },
            traditional: true,
            success: function(data) {
                $('#in-scope-container').empty();
                if (data.cases.length === 0) {
                    $('#in-scope-container').html('<p class="text-light text-center">No test cases found.</p>');
                    return;
                }

                const grouped = {};
                data.cases.forEach(c => {
                    if (!grouped[c.component__name]) grouped[c.component__name] = [];
                    grouped[c.component__name].push(c);
                });

                for (const [modName, cases] of Object.entries(grouped)) {
                    let html = `<div class="module-group" data-module="${modName}">
                                    <div class="module-title"><i class="fa-regular fa-folder text-light"></i> ${modName}</div>`;
                    cases.forEach(c => {
                        html += `
                            <div class="case-item" data-module="${modName}">
                                <input type="checkbox" name="in_scope_cases[]" value="${c.id}" checked class="in-scope-checkbox" id="case-${c.id}">
                                <label for="case-${c.id}" class="font-14" style="cursor: pointer; margin: 0;">
                                    TC-${c.id}: ${c.summary}
                                </label>
                            </div>
                        `;
                    });
                    html += `</div>`;
                    $('#in-scope-container').append(html);
                }
            }
        });
    });

    // 3. Handle Checkbox changes (Move to out-of-scope)
    $(document).on('change', '.in-scope-checkbox', function() {
        if (!$(this).is(':checked')) {
            const caseId = $(this).val();
            const item = $(this).closest('.case-item');
            const label = item.find('label').text();
            const modName = item.data('module');

            item.fadeOut(200, function() {
                $(this).remove();
                if ($('#in-scope-container').children().length === 0) {
                    $('#in-scope-container').html('<p class="text-light text-center">Select Modules to load cases.</p>');
                }
            });

            $('#out-scope-container').append(`
                <div class="case-item out-scope-item" id="out-item-${caseId}" data-module="${modName}">
                    <input type="hidden" name="out_scope_cases[]" value="${caseId}">
                    <button type="button" class="icon-btn text-success restore-btn" title="Restore to In-Scope" style="padding: 0; margin-right: 10px;">
                        <i class="fa-solid fa-rotate-left"></i>
                    </button>
                    <span class="font-14">${label}</span>
                </div>
            `);

            if ($('#out-scope-container').find('.text-center').length > 0) {
                $('#out-scope-container').find('.text-center').remove();
            }
        }
    });

    // 4. Handle Restore button (Move back to in-scope)
    $(document).on('click', '.restore-btn', function() {
        const outItem = $(this).closest('.out-scope-item');
        const caseId = outItem.find('input[type="hidden"]').val();
        const label = outItem.find('span').text();
        const modName = outItem.data('module');

        outItem.fadeOut(200, function() {
            $(this).remove();

            let targetGroup = $(`.module-group[data-module="${modName}"]`);
            if (targetGroup.length === 0) {
                $('#in-scope-container').append(`
                    <div class="module-group" data-module="${modName}">
                        <div class="module-title"><i class="fa-regular fa-folder text-light"></i> ${modName}</div>
                    </div>
                `);
                targetGroup = $(`.module-group[data-module="${modName}"]`);
            }

            targetGroup.append(`
                <div class="case-item" data-module="${modName}">
                    <input type="checkbox" name="in_scope_cases[]" value="${caseId}" checked class="in-scope-checkbox" id="case-${caseId}">
                    <label for="case-${caseId}" class="font-14" style="cursor: pointer; margin: 0;">
                        ${label}
                    </label>
                </div>
            `);

            if ($('#out-scope-container').children().length === 0) {
                $('#out-scope-container').html('<p class="text-light text-center">Excluded test cases will appear here.</p>');
            }
            if ($('#in-scope-container').find('.text-center').length > 0) {
                $('#in-scope-container').find('.text-center').remove();
            }
        });
    });

    // 5. Form validation
    $('#testPlanForm').on('submit', function(e) {
        if ($('.in-scope-checkbox:checked').length === 0) {
            e.preventDefault();
            alert("You must select at least one test case to be In-Scope.");
        }
    });

    // 6. Trigger the pre-selection (Now that the handlers are listening!)
    if (selectedProductId) {
        $('#id_product').val(selectedProductId).trigger('change');
    }
});
