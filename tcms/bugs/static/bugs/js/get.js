import { tagsCard } from '../../../../static/js/tags'
import { treeViewBind } from '../../../../static/js/utils'

export function pageBugsGetReadyHandler () {
    if ($('#page-bugs-get').length === 0) {
        return
    }

    const objectId = $('#object_pk').data('pk')
    const permRemoveTag = $('#object_pk').data('perm-remove-tag') === 'True'

    // bind everything in tags table
    tagsCard('Bug', objectId, { bugs: objectId }, permRemoveTag)

    // executions tree view
    treeViewBind()
}
