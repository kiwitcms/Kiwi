import { jsonRPC } from '../../../../static/js/jsonrpc'
import { markdown2HTML, updateCategorySelectFromProduct } from '../../../../static/js/utils'

export function pageTestcasesMutableReadyHandler () {
    $('#id_template').change(function () {
        window.markdownEditor.codemirror.setValue($(this).val())
    })

    $('#add_id_template').click(function () {
        // note: will not refresh the selected value
        return showRelatedObjectPopup(this)
    })

    if ($('#id_category').find('option').length === 0) {
        populateProductCategory()
    }

    $('#add_id_product').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('#add_id_category').click(function () {
        return showRelatedObjectPopup(this)
    })

    document.getElementById('id_product').onchange = function () {
        $('#id_product').selectpicker('refresh')
        populateProductCategory()
    }

    document.getElementById('id_category').onchange = function () {
        $('#id_category').selectpicker('refresh')
    }

    $('.duration-picker').durationPicker({
        translations: {
            day: $('html').data('trans-day'),
            days: $('html').data('trans-days'),

            hour: $('html').data('trans-hour'),
            hours: $('html').data('trans-hours'),

            minute: $('html').data('trans-minute'),
            minutes: $('html').data('trans-minutes'),

            second: $('html').data('trans-second'),
            seconds: $('html').data('trans-seconds')
        },

        showDays: true,
        showHours: true,
        showMinutes: true,
        showSeconds: true
    })

    const duplicateWarning = $('#duplicate-summary-warning')
    if (duplicateWarning.length) {
        const summaryGroup = $('#summary-group')
        const summaryInput = $('#id_summary')
        const autocomplete = $('#summary-autocomplete')
        const duplicateModal = $('#duplicate-tc-modal')
        const maxItems = 10
        let debounceTimer = null
        let duplicateMatches = []

        function showDuplicateModal (tc) {
            const g = summaryGroup.data.bind(summaryGroup)
            $('#duplicate-tc-modal-title').text(
                g('trans-duplicate-modal-title') + ' - TC-' + tc.id
            )

            // populate header view button
            $('#duplicate-tc-modal-view-btn').attr('href', '/case/' + tc.id + '/')
            $('#duplicate-tc-modal-view-label').text(
                g('trans-duplicate-modal-view') + ' TC-' + tc.id
            )

            const body = $('#duplicate-tc-modal-body')
            body.empty()

            const table = $('<table>', { class: 'table table-striped table-condensed' })
            const rows = [
                [g('trans-duplicate-modal-summary'), tc.summary],
                [g('trans-duplicate-modal-status'), tc.case_status__name],
                [g('trans-duplicate-modal-category'), tc.category__name],
                [g('trans-duplicate-modal-priority'), tc.priority__value],
                [g('trans-duplicate-modal-author'), tc.author__username]
            ]
            rows.forEach(function (row) {
                $('<tr>')
                    .append($('<th>', { text: row[0], css: { width: '150px' } }))
                    .append($('<td>', { text: row[1] || '' }))
                    .appendTo(table)
            })

            const descriptionContainer = $('<div>', {
                class: 'js-duplicate-tc-description',
                css: {
                    'max-height': '300px',
                    'overflow-y': 'auto',
                    'background-color': '#f5f5f5',
                    padding: '10px',
                    'border-radius': '4px'
                }
            })
            const descriptionRow = $('<tr>')
                .append($('<th>', { text: g('trans-duplicate-modal-text'), css: { width: '150px', 'vertical-align': 'top' } }))
                .append($('<td>').append(descriptionContainer))
            table.append(descriptionRow)
            body.append(table)

            if (tc.text) {
                markdown2HTML(tc.text, descriptionContainer[0])
            } else {
                descriptionContainer.text('-')
            }

            duplicateModal.modal('show')
        }

        function updateDuplicateWarning () {
            if (duplicateMatches.length > 0) {
                duplicateWarning.html(
                    '<span class="fa fa-exclamation-triangle"></span> ' +
                    summaryGroup.data('trans-duplicate-blocked')
                ).removeClass('hidden')
            } else {
                duplicateWarning.addClass('hidden').empty()
            }
        }

        summaryInput.on('input', function () {
            const value = $(this).val().trim()
            clearTimeout(debounceTimer)

            if (value.length < 3) {
                duplicateWarning.addClass('hidden').empty()
                autocomplete.hide().empty()
                duplicateMatches = []
                return
            }

            debounceTimer = setTimeout(function () {
                jsonRPC('TestCase.filter', { summary__icontains: value }, function (data) {
                    duplicateMatches = data.filter(function (tc) {
                        return tc.summary.toLowerCase() === value.toLowerCase()
                    })
                    updateDuplicateWarning()

                    autocomplete.empty()
                    if (data.length > 0) {
                        data.slice(0, maxItems).forEach(function (tc) {
                            $('<a>', {
                                href: '#',
                                class: 'list-group-item',
                                text: 'TC-' + tc.id + ': ' + tc.summary
                            }).on('click', function (e) {
                                e.preventDefault()
                                autocomplete.hide()
                                showDuplicateModal(tc)
                            }).appendTo(autocomplete)
                        })
                        if (data.length > maxItems) {
                            $('<span>', {
                                class: 'list-group-item disabled',
                                text: '... and ' + (data.length - maxItems) + ' more'
                            }).appendTo(autocomplete)
                        }
                        autocomplete.show()
                    } else {
                        autocomplete.hide()
                    }
                })
            }, 500)
        })

        $(document).on('click', function (e) {
            if (!$(e.target).closest('#id_summary, #summary-autocomplete').length) {
                autocomplete.hide()
            }
        })

        summaryInput.on('focus', function () {
            if (autocomplete.children().length > 0) {
                autocomplete.show()
            }
        })

        duplicateWarning.closest('form').on('submit', function (e) {
            const currentValue = summaryInput.val().trim()
            if (currentValue.length < 1) {
                return
            }

            // synchronous server-side case-insensitive exact match check
            duplicateMatches = []
            jsonRPC('TestCase.filter', { summary__iexact: currentValue }, function (data) {
                duplicateMatches = data
            }, true)

            if (duplicateMatches.length > 0) {
                e.preventDefault()
                updateDuplicateWarning()
                showDuplicateModal(duplicateMatches[0])
                return false
            }
        })
    }
}

function populateProductCategory () {
    const productId = $('#id_product').val()

    if (productId === null) {
        $('#add_id_category').addClass('disabled')
    } else {
        $('#add_id_category').removeClass('disabled')
    }

    const href = $('#add_id_category')[0].href
    $('#add_id_category')[0].href = href.slice(0, href.indexOf('&product'))
    $('#add_id_category')[0].href += `&product=${productId}`
    $('#id_category').find('option').remove()
    updateCategorySelectFromProduct()
}
