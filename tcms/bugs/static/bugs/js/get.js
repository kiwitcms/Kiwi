$(document).ready(function() {
    var object_id = $('#object_pk').data('pk');
    var perm_remove_tag = $('#object_pk').data('perm-remove-tag') === 'True';

    // bind everything in tags table
    tagsCard('Bug', object_id, {bugs: object_id}, perm_remove_tag);

    // executions tree view
    treeViewBind();
});
