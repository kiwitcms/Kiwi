import { jsonRPC } from '../../../../../static/js/jsonrpc'
import { updateSelect } from '../../../../../static/js/utils'

export function loadInitialProduct (callback = () => {}) {
    jsonRPC('Product.filter', {}, data => {
        updateSelect(data, '#id_product', 'id', 'name', null)
        callback()
    })
}

export function showOnlyRoundNumbers (number) {
    return number % 1 === 0 ? number : ''
}
