// Copyright (c) 2023-2026 Alexander Todorov <atodorov@otb.bg>

// Licensed under the GPL 2.0 or later: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

function fitTableToPage (doc) {
    const table = doc.content[doc.content.length - 1].table
    const columnCount = table.body[0].length
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    const widths = []
    const headerFontSize = doc.styles.tableHeader.fontSize || 11
    const bodyFontSize = doc.defaultStyle.fontSize || 10

    for (let column = 0; column < columnCount; column++) {
        const header = table.body[0][column]
        const headerText = header && typeof header === 'object' ? header.text : header
        let longest = ''

        for (let row = 1; row < table.body.length; row++) {
            const cell = table.body[row][column]
            const text = cell && typeof cell === 'object' ? cell.text : cell
            const value = String(text ?? '')

            if (value.length > longest.length) {
                longest = value
            }
        }

        context.font = `bold ${headerFontSize}pt sans-serif`
        const headerWidth = context.measureText(String(headerText ?? '')).width

        context.font = `${bodyFontSize}pt sans-serif`
        const bodyWidth = context.measureText(longest).width

        widths.push(Math.max(headerWidth, bodyWidth))
    }

    const horizontalPadding = 8 * columnCount - 8
    const availableWidth = 1190.55 - doc.pageMargins[0] - doc.pageMargins[2] - horizontalPadding
    const totalWidth = widths.reduce((sum, width) => sum + width, 0)

    if (totalWidth < availableWidth) {
        table.widths = widths.map(width => width * availableWidth / totalWidth)
    }
}

export const exportButtons = [
    {
        extend: 'csv',
        exportOptions: {
            columns: ':visible:not(.noVis)'
        },
        text: '<i class="fa fa-th-list" aria-hidden="true"></i>',
        titleAttr: 'CSV'
    },
    {
        extend: 'excel',
        exportOptions: {
            columns: ':visible:not(.noVis)'
        },
        text: '<i class="fa fa-file-excel-o" aria-hidden="true"></i>',
        titleAttr: 'Excel'
    },
    {
        extend: 'pdf',
        pageSize: 'A3',
        orientation: 'landscape',
        customize: function (doc) {
            doc.pageMargins = [10, 10, 10, 10]
            fitTableToPage(doc)
        },
        exportOptions: {
            columns: ':visible:not(.noVis)'
        },
        text: '<i class="fa fa-file-pdf-o" aria-hidden="true"></i>',
        titleAttr: 'PDF'
    },
    {
        extend: 'print',
        exportOptions: {
            columns: ':visible:not(.noVis)'
        },
        text: '<i class="fa fa-print" aria-hidden="true"></i>',
        titleAttr: 'Print'
    },
    {
        extend: 'colvis',
        collectionLayout: 'fixed columns',
        columns: ':not(.noVis)',
        text: '<i class="fa fa-eye" aria-hidden="true"></i>',
        titleAttr: 'Column visibility'
    }
]
