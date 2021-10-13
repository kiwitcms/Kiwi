/*
    Applies tag to the chosen model

    @model - string - model name which accepts tags. There must
        be a 'MM.add_tag' RPC function for this to work!
    @objectId - int - PK of the object that will be tagged
    @tagInput - jQuery object - usually an <input> element which
        provides the value used for tagging
    @toTable - DataTable object - the table which displays the results
*/
function addTag (model, objectId, tagInput, toTable) {
  const tagName = tagInput.value

  if (tagName.length > 0) {
    jsonRPC(model + '.add_tag', [objectId, tagName], function (data) {
      toTable.row.add({ name: tagName }).draw()
      $(tagInput).val('')
    })
  }
}

/*
    Displays the tags table inside a card and binds all buttons
    and actions for it.

    @model - string - model name which accepts tags. There must
        be a 'MM.add_tag' RPC function for this to work!
    @objectId - int - PK of the object that will be tagged
    @displayFilter - dict - passed directly to `Tag.filter` to display
        tags for @objectId
    @permRemove - bool - if we have permission to remove tags

*/
function tagsCard (model, objectId, displayFilter, permRemove) {
  // load the tags table
  const tagsTable = $('#tags').DataTable({
    ajax: function (data, callback, settings) {
      dataTableJsonRPC('Tag.filter', displayFilter, callback, function (data, callback) {
        // b/c tags are now annotated with case, run, plan IDs there are duplicate names.
        // Filter them out by only looking at Tag.id uniqueness!
        data = arrayToDict(data)
        callback({ data: Object.values(data) })
      })
    },
    columns: [
      { data: 'name' },
      {
        data: null,
        sortable: false,
        render: function (data, type, full, meta) {
          if (permRemove) {
            return '<a href="#tags" class="remove-tag" data-name="' + data.name + '"><span class="pficon-error-circle-o hidden-print"></span></a>'
          }
          return ''
        }
      }
    ],
    dom: 't',
    language: {
      loadingRecords: '<div class="spinner spinner-lg"></div>',
      processing: '<div class="spinner spinner-lg"></div>',
      zeroRecords: 'No records found'
    },
    order: [[0, 'asc']]
  })

  // remove tags button
  tagsTable.on('draw', function () {
    $('.remove-tag').click(function () {
      const tr = $(this).parents('tr')

      jsonRPC(model + '.remove_tag', [objectId, $(this).data('name')], function (data) {
        tagsTable.row($(tr)).remove().draw()
      })
    })
  })

  // add tag button and Enter key
  $('#add-tag').click(function () {
    addTag(model, objectId, $('#id_tags')[0], tagsTable)
  })

  $('#id_tags').keyup(function (event) {
    if (event.keyCode === 13) {
      addTag(model, objectId, $('#id_tags')[0], tagsTable)
    };
  })

  // tag autocomplete
  $('#id_tags.typeahead').typeahead({
    minLength: 3,
    highlight: true
  }, {
    name: 'tags-autocomplete',
    // will display up to X results even if more were returned
    limit: 100,
    async: true,
    display: function (element) {
      return element.name
    },
    source: function (query, processSync, processAsync) {
      jsonRPC('Tag.filter', { name__icontains: query }, function (data) {
        // b/c tags are now annotated with case, run, plan IDs there are duplicate names.
        // Filter them out by only looking at Tag.id uniqueness!
        data = arrayToDict(data)
        return processAsync(Object.values(data))
      })
    }
  })
}
