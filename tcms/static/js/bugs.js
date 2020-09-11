const bugDetailsCache = {}

function loadBugs(selector, filter) {
    const noRecordsFoundText = $('.bugs-table').data('no-records-found-text')

    $(selector).DataTable({
        ajax: (data, callback, settings) => {
            dataTableJsonRPC('TestExecution.get_links', filter, callback);
        },
        columns: [
            {
                data: null,
                render: (data, type, full, meta) => `<a href="${data.url}" class="bug-url">${data.url}</a>`
            },
            {
                data: null,
                render: (data, type, full, meta) => `<a href="#bugs" data-toggle="popover" data-html="true"
                        data-content="undefined" data-trigger="focus" data-placement="top">
                        <span class="fa fa-info-circle"></span>
                        </a>`
            },
        ],
        dom: "t",
        language: {
            loadingRecords: '<div class="spinner spinner-lg"></div>',
            processing: '<div class="spinner spinner-lg"></div>',
            zeroRecords: noRecordsFoundText
        },
        order: [[0, 'asc']],
    });

    $(selector).on('draw.dt', () => {
        $(selector).find('[data-toggle=popover]')
            .popovers()
            .on('show.bs.popover', (element) => {
                fetchBugDetails(
                    $(element.target).parents('tr').find('.bug-url')[0],
                    element.target);
            });
    });

    $('[data-toggle=popover]')
        .popovers()
        .on('show.bs.popover', (element) => {
            fetchBugDetails(
                $(element.target).parents('.list-view-pf-body').find('.bug-url')[0],
                element.target
            );
        });
}

function fetchBugDetails(source, popover, cache = bugDetailsCache) {
    if (source.href in cache) {
        assignPopoverData(source, popover, cache[source.href]);
        return;
    }

    jsonRPC('Bug.details', [source.href], data => {
        cache[source.href] = data;
        assignPopoverData(source, popover, data);
    }, true);
}

function assignPopoverData(source, popover, data) {
    source.title = data.title;
    $(popover).attr('data-original-title', data.title);
    $(popover).attr('data-content', data.description);
}
