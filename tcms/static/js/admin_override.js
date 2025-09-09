$(() => {
    $('#change-history').addClass('grp-table')

    $('#logout_link').click(function () {
        $('#logout_form').submit()
        return false
    })
})
