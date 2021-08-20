$(document).ready(function () {
  const objectId = $('#object_pk').data('pk')
  const permRemoveTag = $('#object_pk').data('perm-remove-tag') === 'True'

  // bind everything in tags table
  tagsCard('Bug', objectId, { bugs: objectId }, permRemoveTag)

  // executions tree view
  treeViewBind()
})
