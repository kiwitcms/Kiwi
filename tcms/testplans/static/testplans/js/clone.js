// Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

// Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import { jsonRPC } from '../../../../static/js/jsonrpc'
import { populateVersion } from '../../../../static/js/utils'

function syncOtherProductSelects (current, productId, productName) {
    $('select.js-product').not(current).each(function (index, select) {
        select.add(new Option(productName, productId))
        $(select).selectpicker('refresh')
    })
}

function syncOtherVersionSelects (current, productId, versionId, versionName) {
    $('select.js-version').not(current).each(function (index, select) {
        const row = $(select).closest('.js-clone-row')

        if (row.find('select.js-product').val() === productId) {
            select.add(new Option(versionName, versionId))
            $(select).selectpicker('refresh')
        }
    })
}

function rowValues (row) {
    const values = {
        name: row.find('input.js-name').val(),
        product: Number(row.find('select.js-product').val()),
        version: Number(row.find('select.js-version').val()),
        copy_testcases: row.find('input.js-copy-testcases').is(':checked')
    }

    if (row.find('input.js-parent').is(':checked')) {
        values.parent = Number(row.find('input.js-parent').val())
    }

    return values
}

function showRowError (row, message) {
    row.find('.js-clone-error-text').text(message)
    row.find('.js-clone-error').removeClass('hidden')
    $('#js-clone-button').button('reset')
}

export function pageTestplansCloneReadyHandler () {
    const dismissAddRelatedObjectPopup = window.dismissAddRelatedObjectPopup

    window.dismissAddRelatedObjectPopup = function (win, newId, newRepr, optgroup) {
        const current = document.getElementById(win.name)

        if (current && $(current).hasClass('js-product')) {
            syncOtherProductSelects(current, newId, newRepr)
        } else if (current && $(current).hasClass('js-version')) {
            const row = $(current).closest('.js-clone-row')
            const productId = row.find('select.js-product').val()

            syncOtherVersionSelects(current, productId, newId, newRepr)
        }

        return dismissAddRelatedObjectPopup.apply(window, arguments)
    }

    $('.js-add-product').click(function () {
        return showRelatedObjectPopup(this)
    })

    $('.js-add-version').click(function () {
        return showRelatedObjectPopup(this)
    })

    // NOTE: use the native onchange property, NOT $(...).change()
    $('select.js-product').each(function () {
        this.onchange = function () {
            $(this).selectpicker('refresh')

            const row = $(this).closest('.js-clone-row')

            populateVersion(
                row.find('select.js-product'),
                row.find('select.js-version'),
                row.find('.js-add-version')
            )
        }
    })

    $('select.js-version').each(function () {
        this.onchange = function () {
            $(this).selectpicker('refresh')
        }
    })

    const cloneButton = $('#js-clone-button')
    cloneButton.click(function () {
        const isTree = $('#main-element').data('is-tree') === 1
        const rows = $('.js-clone-row').not('.js-cloned')
        // maps the id of a source TestPlan to the id of its clone
        const clonedPlanIds = {}

        const cloneIsDone = function () {
            const newPlanIds = Object.values(clonedPlanIds)

            if (newPlanIds.length < rows.length) {
                return
            }

            const redirectToClonedPlan = function () {
                if (isTree || newPlanIds.length === 1) {
                    window.location.assign(`/plan/${newPlanIds[0]}/`)
                } else {
                    window.location.assign(document.referrer || '/')
                }
            }

            // in tree mode set the parent of every clone, which can only be
            // done once all of the clones have been created.
            if (isTree) {
                let updatedCount = 0

                const updateIsDone = function () {
                    updatedCount += 1

                    if (updatedCount === rows.length) {
                        redirectToClonedPlan()
                    }
                }

                rows.each(function () {
                    const row = $(this)

                    jsonRPC(
                        'TestPlan.update',
                        [
                            clonedPlanIds[row.data('plan-id')],
                            { parent: clonedPlanIds[row.attr('data-parent-id')] }
                        ],
                        updateIsDone
                    )
                })

                return
            }

            redirectToClonedPlan()
        }

        if (!rows.length) {
            cloneButton.button('reset')
            return
        }

        cloneButton.button('loading')

        rows.each(function () {
            const row = $(this)
            row.find('.js-clone-error').addClass('hidden')

            const values = rowValues(row)

            jsonRPC('TestPlan.clone', [row.data('plan-id'), values], function (result) {
                clonedPlanIds[row.data('plan-id')] = result.id
                row.addClass('js-cloned')
                row.find('.js-clone-ok').removeClass('hidden')
                cloneIsDone()
            }, false, function (message) {
                showRowError(row, message)
            })
        })
    })
}
