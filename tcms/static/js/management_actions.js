Nitrate.Management = {};
Nitrate.Management.Environment = {};
Nitrate.Management.Environment.Edit = {};
Nitrate.Management.Environment.Property = {};

Nitrate.Management.Environment.Edit.on_load = function() {
  SelectFilter.init("id_properties", "properties", 0, "/static/admin/");
};

Nitrate.Management.Environment.on_load = function() {
  jQ('.js-add-env-group').bind('click', function() {
    addEnvGroup();
  });

  jQ('.js-del-env-group').bind('click', function() {
    var params = jQ(this).parents('.js-env-group').data('params');
    deleteEnvGroup(params[0], params[1]);
  });

};

Nitrate.Management.Environment.Property.on_load = function() {
  jQ('#js-add-prop').bind('click', function() {
    addEnvProperty();
  });
  jQ('#js-disable-prop').bind('click', function() {
    disableEnvProperty();
  });
  jQ('#js-enable-prop').bind('click', function() {
    enableEnvProperty();
  });
  jQ('.js-prop-name').bind('click', function() {
    selectEnvProperty(jQ(this).parents('.js-one-prop').data('param'));
  });
  jQ('.js-edit-prop').bind('click', function() {
    editEnvProperty(jQ(this).parents('.js-one-prop').data('param'));
  });
};

function addEnvGroup() {
  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    if (returnobj.rc === 0) {
      if (returnobj.id) {
        window.location.href = Nitrate.Management.Environment.Param.edit_group + '?id=' + returnobj.id;
      }
      return true;
    } else {
      window.alert(returnobj.response);
      return false;
    }
  };

  var group_name = window.prompt("New environment group name");

  if (group_name) {
    jQ.ajax({
      'url': Nitrate.Management.Environment.Param.add_group,
      'type': 'GET',
      'data': {'action': 'add', 'name': group_name},
      'success': function (data, textStatus, jqXHR) {
        success(jqXHR);
      }
    });
  }
}

function deleteEnvGroup(id, env_group_name) {
  var answer = window.confirm("Are you sure you wish to remove environment group - " + env_group_name);

  if (!answer) {
    return false;
  }

  var url = Nitrate.Management.Environment.Param.delete_group + '?action=del&id=' + id;
  jQ.ajax({
    'url': url,
    'type': 'GET',
    'complete': function (jqXHR, textStatus) {
      var returnobj = jQ.parseJSON(jqXHR.responseText);
      if (returnobj.rc === 1) {
        window.alert(returnobj.response);
      } else {
        jQ('#' + id).remove();
      }
    }
  });
}

function selectEnvProperty(property_id) {
  jQ('#id_properties_container li.focus').removeClass('focus');
  jQ('#id_property_' + property_id).addClass('focus');

  jQ.ajax({
    'url': Nitrate.Management.Environment.Property.Param.list_property_values,
    'type': 'GET',
    'data': {'action': 'list', 'property_id': property_id},
    'success': function (data, textStatus, jqXHR) {
      jQ('#' + 'id_values_container').html(data);
      bindPropertyValueActions();
    }
  });
}

function addEnvProperty() {
  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    if (returnobj.rc === 0) {
      jQ('#id_properties_container li.focus').removeClass('focus');

      var id = returnobj.id;
      var name = returnobj.name;
      var template = Handlebars.compile(jQ('#properties_container_template').html());
      var context = {'id': id, 'name': name};
      jQ('#id_properties_container').append(template(context))
        .find('.js-prop-name').bind('click', function() {
          selectEnvProperty(jQ(this).parent().data('param'));
        })
        .end().find('.js-edit-prop').bind('click', function() {
          editEnvProperty(jQ(this).parents('.js-one-prop').data('param'));
        });

      selectEnvProperty(id);
    } else {
      window.alert(returnobj.response);
      return false;
    }
  };

  var property_name = window.prompt("New property name");

  if(property_name) {
    jQ.ajax({
      'url': Nitrate.Management.Environment.Property.Param.add_property,
      'type': 'GET',
      'data': {'action': 'add', 'name': property_name},
      'success': function (data, textStatus, jqXHR) {
        success(jqXHR);
      }
    });
  }
}

function editEnvProperty(id) {
  var new_property_name = window.prompt("New property name", jQ('#id_property_name_' + id).html());

  var success = function(t) {
    returnobj = jQ.parseJSON(t.responseText);

    if (returnobj.rc === 0) {
      jQ('#id_property_name_' + id).html(new_property_name);
    } else {
      window.alert(returnobj.response);
      return false;
    }
  };

  if (new_property_name) {
    jQ.ajax({
      'url': Nitrate.Management.Environment.Property.Param.edit_property,
      'type': 'GET',
      'data': {'action': 'edit', 'id': id, 'name': new_property_name},
      'success': function (data, textStatus, jqXHR) {
        success(jqXHR);
      }
    });
  }
}


function enableEnvProperty() {
  if (!jQ('#id_properties_container input[name="id"]:checked').length) {
    window.alert("Please click the checkbox to choose properties");
    return false;
  }

  window.location.href = Nitrate.Management.Environment.Property.Param.modify_property
    + '?action=modify&status=1&' + jQ('#id_property_form').serialize();
}


function disableEnvProperty() {
  if(!jQ('#id_properties_container input[name="id"]:checked').length) {
    window.alert("Please click the checkbox to choose properties");
    return false;
  }
  window.location.href = Nitrate.Management.Environment.Property.Param.modify_property
    + '?action=modify&status=0&' + jQ('#id_property_form').serialize();
}

function addEnvPropertyValue(property_id) {
  var value_name = jQ('#id_value_name').val();

  if (!value_name.replace(/\040/g, "").replace(/%20/g, "").length) {
    window.alert('Value name could not be blank or space.');
    return false;
  }

  if (value_name) {
    jQ.ajax({
      'url': Nitrate.Management.Environment.Property.Param.add_property_value,
      'type': 'GET',
      'data': {'action': 'add', 'property_id': property_id, 'value': value_name},
      'success': function (data, textStatus, jqXHR) {
        jQ('#id_values_container').html(data);
        bindPropertyValueActions();
      }
    });
  }
}

function editEnvPropertyValue(property_id, value_id) {
  var value_name = prompt('New value name', jQ('#id_value_' + value_id).html());

  if (value_name) {
    jQ.ajax({
      'url': Nitrate.Management.Environment.Property.Param.add_property_value,
      'type': 'GET',
      'data': {'action': 'edit', 'property_id': property_id, 'id': value_id, 'value': value_name},
      'success': function (data, textStatus, jqXHR) {
        jQ('#id_values_container').html(data);
        bindPropertyValueActions();
      }
    });
  }
}

function getPropValueId() {
  var ids = [];
  jQ('#id_value_form').serializeArray().forEach(function(param) {
    if(param.name === 'id') {
      ids.push(param.value);
    }
  });
  if (ids.length === 1) {
    return ids[0];
  }
  return ids;
}

function enableEnvPropertyValue(property_id) {
  if(!jQ('#id_values_container input[name="id"]:checked').length) {
    window.alert('Please click the checkbox to choose properties');
    return false;
  }

  jQ.ajax({
    'url': Nitrate.Management.Environment.Property.Param.add_property_value,
    'type': 'GET',
    'data': {'action': 'modify', 'property_id': property_id, 'status': 1,
    'id': getPropValueId()},
    'success': function (data, textStatus, jqXHR) {
      jQ('#id_values_container').html(data);
      bindPropertyValueActions();
    }
  });
}

function disableEnvPropertyValue(property_id) {
  if (!jQ('#id_values_container input[name="id"]:checked').length) {
    window.alert('Please click the checkbox to choose properties');
    return false;
  }

  jQ.ajax({
    'url': Nitrate.Management.Environment.Property.Param.add_property_value,
    'type': 'GET',
    'data': {'action': 'modify', 'property_id': property_id, 'status': 0,
    'id': getPropValueId()},
    'success': function (data, textStatus, jqXHR) {
      jQ('#id_values_container').html(data);
      bindPropertyValueActions();
    }
  });
}

function bindPropertyValueActions() {
  var propId = jQ('.js-prop-value-action').data('param');
  jQ('#js-add-prop-value').bind('click', function() {
    addEnvPropertyValue(propId);
  });
  jQ('#js-disable-prop-value').bind('click', function() {
    disableEnvPropertyValue(propId);
  });
  jQ('#js-enable-prop-value').bind('click', function() {
    enableEnvPropertyValue(propId);
  });
  jQ('.js-edit-prop-value').bind('click', function() {
    editEnvPropertyValue(propId, jQ(this).data('param'));
  });
}
