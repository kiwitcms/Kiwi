export function initializeDateTimePicker (selector) {
    $(selector).datetimepicker({
        locale: $('html').attr('lang'),
        format: 'YYYY-MM-DD',
        allowInputToggle: true,
        showTodayButton: true,
        icons: {
            today: 'today-button-pf'
        }
    })
};
