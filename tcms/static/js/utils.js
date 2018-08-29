/*
    Used to update a Version select when Product changes.
*/
function updateVersionSelect(data) {
    // the zero-th option is a special one
    var new_options = $('#id_version')[0].options[0].outerHTML;
    data.forEach(function(element) {
        new_options += '<option value="' + element.id + '">' + element.value + '</option>';
    });
    $('#id_version')[0].innerHTML = new_options;
    $('#id_version').selectpicker('refresh');
}


/*
    Used to update a Build select when Product changes.
*/
function updateBuildSelect(data) {
    // the zero-th option is a special one
    var new_options = $('#id_build')[0].options[0].outerHTML;
    data.forEach(function(element) {
        new_options += '<option value="' + element.build_id + '">' + element.name + '</option>';
    });
    $('#id_build')[0].innerHTML = new_options;
    $('#id_build').selectpicker('refresh');
}
