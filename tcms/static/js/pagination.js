// hooks events into DataTable pagination controls
function hookIntoPagination(tableSelector, table) {
    var updateCurrentPage = function(table) {
        var info = table.page.info();
        $('.current-page').val(info.page+1);
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

    $(tableSelector).on('init.dt', function() {
        var info = table.page.info();
        $('.total-pages').html(info.pages);
    });
}
