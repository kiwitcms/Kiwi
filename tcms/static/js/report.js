Nitrate.Report = {};
Nitrate.Report.List = {};
Nitrate.Report.CustomSearch = {};
Nitrate.Report.CustomDetails = {};

Nitrate.Report.List.on_load = function(){
	
}

Nitrate.Report.Builds = {};

Nitrate.Report.Builds.on_load = function() {
  if (jQ('#report_build').length) {
    jQ('#report_build').dataTable({
      "bPaginate": false,
      "bFilter": false,
      "bProcessing": true,
      "oLanguage": { "sEmptyTable": "No build was found in this product." }
    });
  }
};

Nitrate.Report.CustomSearch.on_load = function() {
  if (jQ('#id_pk__in').length) {
    bind_build_selector_to_product(false, jQ('#id_product')[0], jQ('#id_pk__in')[0]);
  }

  if (jQ('#id_build_run__product_version').length) {
    bind_version_selector_to_product(true, false, jQ('#id_product')[0], jQ('#id_build_run__product_version')[0]);
  }

  if (jQ('#id_testcaserun__case__category').length) {
    bind_category_selector_to_product(true, false, jQ('#id_product')[0], jQ('#id_testcaserun__case__category')[0]);
  }

  if (jQ('#id_testcaserun__case__component').length) {
    bind_component_selector_to_product(true, false, jQ('#id_product')[0], jQ('#id_testcaserun__case__component')[0]);
  }

  if (jQ('#id_table_report').length) {
    jQ('#id_table_report').dataTable({
      "aoColumnDefs":[{ "sType": "numeric", "aTargets": [1, 2, 3, 4, 5 ] }],
      "bPaginate": false,
      "bFilter": false,
      "bProcessing": true,
      "oLanguage": { "sEmptyTable": "No report data was found." }
    });
  }

  jQ('.build_link').bind('click', function(e) {
    e.stopPropagation();
    e.preventDefault();
    var params = Nitrate.Utils.formSerialize(jQ('#id_form_search')[0]);
    var build_id = jQ(this).siblings().eq(0).val();
    params.pk__in = build_id;
        
    postToURL(this.href, params, 'get');
  });
};

Nitrate.Report.CustomDetails.on_load = function() {
  if (jQ('#id_pk__in').length) {
    bind_build_selector_to_product(false, jQ('#id_product')[0], jQ('#id_pk__in')[0]);
  }

  if (jQ('#id_build_run__product_version').length) {
    bind_version_selector_to_product(true, false, jQ('#id_product')[0], jQ('#id_build_run__product_version')[0]);
  }
};
