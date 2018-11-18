Nitrate.Report = {};
Nitrate.Report.List = {};
Nitrate.Report.CustomSearch = {};
Nitrate.Report.CustomDetails = {};
Nitrate.Report.Builds = {};
Nitrate.Report.TestingReport = {};


Nitrate.Report.Builds.on_load = function() {
  if ($('#report_build').length) {
    $('#report_build').DataTable({
      "bPaginate": false,
      "bFilter": false,
      "bProcessing": true,
      "oLanguage": { "sEmptyTable": "No build was found in this product." }
    });
  }
};


Nitrate.Report.CustomSearch.on_load = function() {
    $('#id_product').change(update_version_select_from_product);
    if (!$('#id_version').val().length) {
        update_version_select_from_product();
    }

    $('#id_product').change(update_build_select_from_product);
    if (!$('#id_build').val().length) {
        update_build_select_from_product();
    }

    $('#id_product').change(update_category_select_from_product);
    if (!$('#id_category').val().length) {
        update_category_select_from_product();
    }

    $('#id_product').change(update_component_select_from_product);
    if (!$('#id_component').val().length) {
        update_component_select_from_product();
    }

  if ($('#id_table_report').length) {
    $('#id_table_report').DataTable({
      "aoColumnDefs":[{ "sType": "numeric", "aTargets": [1, 2, 3, 4, 5 ] }],
      "bPaginate": false,
      "bFilter": false,
      "bProcessing": true,
      "oLanguage": { "sEmptyTable": "No report data was found." }
    });
  }

  $('.build_link').bind('click', function(e) {
    e.stopPropagation();
    e.preventDefault();
    var params = Nitrate.Utils.formSerialize($('#id_form_search')[0]);
    var build_id = $(this).siblings().eq(0).val();
    params.build = build_id;

    postToURL(this.href, params, 'get');
  });
};

Nitrate.Report.CustomDetails.on_load = function() {
    $('#id_product').change(update_version_select_from_product);
    $('#id_product').change(update_build_select_from_product);
};


Nitrate.Report.TestingReport.on_load = function() {
    $('#id_product').change(function() {
        $('#id_version').find('option').remove();
        update_version_select_from_product($(this))
    });
    if (!$('#id_version').val().length) {
        update_version_select_from_product();
    }

    $('#id_product').change(update_build_select_from_product);
    if (!$('#id_build').val().length) {
        update_build_select_from_product();
    }
}
