export const exportButtons = [
    {
        extend: 'csv',
        text: '<i class="fa fa-th-list" aria-hidden="true"></i>',
        titleAttr: 'CSV'
    },
    {
        extend: 'excel',
        text: '<i class="fa fa-file-excel-o" aria-hidden="true"></i>',
        titleAttr: 'Excel'
    },
    {
        extend: 'pdf',
        text: '<i class="fa fa-file-pdf-o" aria-hidden="true"></i>',
        titleAttr: 'PDF'
    },
    {
        extend: 'print',
        text: '<i class="fa fa-print" aria-hidden="true"></i>',
        titleAttr: 'Print'
    },
    {
        extend: 'colvis',
        collectionLayout: 'fixed columns',
        columns: ':not(.noVis)',
        text: '<i class="fa fa-eye" aria-hidden="true"></i>',
        titleAttr: 'Column visibility'
    },
]
