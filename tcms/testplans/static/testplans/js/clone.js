// Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

// Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import { jsonRPC } from '../../../../static/js/jsonrpc'
import { populateVersion } from '../../../../static/js/utils'

export function pageTestplansCloneReadyHandler () {
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
        const rows = $('.js-clone-row').not('.js-cloned')
        const clonedPlanIds = []

        const cloneIsDone = function () {
            if (clonedPlanIds.length < rows.length) {
                return
            }

            if (clonedPlanIds.length === 1) {
                window.location.assign(`/plan/${clonedPlanIds[0]}/`)
            } else {
                window.location.assign(document.referrer || '/')
            }
        }

        if (!rows.length) {
            cloneButton.button('reset')
            return
        }

        cloneButton.button('loading')

        rows.each(function () {
            const row = $(this)
            row.find('.js-clone-error').addClass('hidden')

            const values = {
                name: row.find('input.js-name').val(),
                product: Number(row.find('select.js-product').val()),
                version: Number(row.find('select.js-version').val()),
                copy_testcases: row.find('input.js-copy-testcases').is(':checked')
            }

            if (row.find('input.js-parent').is(':checked')) {
                values.parent = Number(row.find('input.js-parent').val())
            }

            jsonRPC('TestPlan.clone', [row.data('plan-id'), values], function (result) {
                clonedPlanIds.push(result.id)
                row.addClass('js-cloned')
                row.find('.js-clone-ok').removeClass('hidden')
                cloneIsDone()
            }, false, function (message) {
                row.find('.js-clone-error-text').text(message)
                row.find('.js-clone-error').removeClass('hidden')
                cloneButton.button('reset')
            })
        })
    })
}
