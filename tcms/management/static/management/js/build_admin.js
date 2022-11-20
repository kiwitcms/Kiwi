import { updateVersionSelectFromProduct } from '../../../../static/js/utils'

export function pageManagementBuildAdminReadyHandler () {
    const filterParams = new URLSearchParams(window.location.search)

    $('#id_product').change(updateVersionSelectFromProduct)
    $('#id_version').change(() => {
        if (filterParams.has('version')) {
            const version = filterParams.get('version')
            $(`#id_version > option[value=${version}]`).attr('selected', true)
        }
    })

    if (filterParams.has('product')) {
        $('#id_product').change()
    }
}
