Nitrate.Profiles = { Infos: {}, Bookmarks: {} };

Nitrate.Profiles.Bookmarks.on_load = function() {
  if (jQ('#id_table_bookmark').length) {
    jQ('#id_table_bookmark').dataTable({
      "aoColumnDefs":[{ "bSortable":false, "aTargets":[ 0 ] }],
      "aaSorting": [[ 1, "asc" ]],
      "sPaginationType": "full_numbers",
      "bFilter": false,
      "aLengthMenu": [[10, 20, 50, -1], [10, 20, 50, "All"]],
      "iDisplayLength": 10,
      "bProcessing": true,
      "oLanguage": { "sEmptyTable": "No bookmark was found." }
    });
  }

  if (jQ('#id_check_all_bookmark').length) {
    jQ('#id_check_all_bookmark').bind('click', function(e) {
      clickedSelectAll(this, jQ('#id_table_bookmark')[0], 'pk');
    });
  }

  jQ('#id_form_bookmark').bind('submit', function(e) {
    e.stopPropagation();
    e.preventDefault();

    if (!window.confirm(default_messages.confirm.remove_bookmark)) {
      return false;
    }

    var callback = function(t) {
      var returnobj = jQ.parseJSON(t.responseText);

      if (returnobj.rc != 0) {
        window.alert(returnobj.response);
        return returnobj;
      }
      // using location.reload will cause firefox(tested) remember the checking status
      window.location = window.location;
    };
    var parameters = Nitrate.Utils.formSerialize(this);
    if (!parameters['pk']) {
      window.alert('No bookmark selected.');
      return false;
    }
    removeBookmark(this.action, this.method, parameters, callback);
  });
};

function removeBookmark(url, method, parameters, callback) {
  jQ.ajax({
    'url': url,
    'type': method,
    'data': parameters,
    'traditional': true,
    'success': function (data, textStatus, jqXHR) {
      callback(jqXHR);
    },
    'error': function (jqXHR, textStatus, errorThrown) {
      json_failure(jqXHR);
    }
  });
}
