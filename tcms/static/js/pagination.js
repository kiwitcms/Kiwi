// hooks events into DataTable pagination controls
function hookIntoPagination(tableSelector, table) {
    var updateCurrentPage = function(table) {
        var info = table.page.info();
        $('.current-page').val(info.page+1);
        $('.total-pages').html(info.pages);

        if (info.page === 0) {
            $('.pagination-pf-back').find('li').addClass('disabled');
        } else {
            $('.pagination-pf-back').find('li').removeClass('disabled');
        }

        if (info.page === info.pages-1) {
            $('.pagination-pf-forward').find('li').addClass('disabled');
        } else {
            $('.pagination-pf-forward').find('li').removeClass('disabled');
        }
    };

    // hook into pagination controls
    $('.next-page').click(function(){
        table.page('next').draw('page');
    });

    $('.last-page').click(function(){
        table.page('last').draw('page');
    });

    $('.previous-page').click(function(){
        table.page('previous').draw('page');
    });

    $('.first-page').click(function(){
        table.page('first').draw('page');
    });

    // updates after page change
    $(tableSelector).on('page.dt', function() {
        updateCurrentPage(table);
    });

    // updates after sort
    $(tableSelector).on('order.dt', function() {
        updateCurrentPage(table);
    });

    // hide the select checkboxes if not in use
    if (window.location.href.indexOf('allow_select') === -1) {
        $(tableSelector).on('draw.dt', function() {
            $('.js-select-checkbox').hide();
        });
    }
}
