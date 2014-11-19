// Create a namespace that can hold all code for the "create run" page:
Nitrate.CreateRunPage = {
  has_user_edited_name : false,

  /* Page-loading callback: */
  on_load : function() {
    /*
        Wire up the <select> elements.
        They may not be blank.
    */
    bind_build_selector_to_product(false);
    // bind_env_selector_to_product(false);
    bind_version_selector_to_product(false);

    /*
        NewRun_Name_autofill: the new run page shall contain a field for
        entering the name of the new plan. If the user has not touched the
        field, the field shall automatically populate with text of the form:
          * (planname):(environmentname):(number of runs made with this plan/environment combo) 

        and the field shall update as environments are selected, until the
        user manually edits the field. For example, a sample value might read:
          "OpenGL Performance:x86_64:001"
    */

    // FIXME: Re-enable here after finish the new environment

    /*
    if($('id_env_id')) {
        $('id_env_id').observe('change', Nitrate.CreateRunPage.autofill_name);
    }
    */


    // Once the user manually touches the summary field, stop auto-filling it:
    jQ('#id_summary').bind('change', function() {
      Nitrate.CreateRunPage.has_user_edited_name = true;
    });

    // Autofill the summary if it doesn't yet have a value:
    // FIXME: Re-enable here after finish the new environment
    /*
    if ($('id_summary').value=='') {
        Nitrate.CreateRunPage.autofill_name();
    }
    */
  },

  autofill_name : function() {
    if (!Nitrate.CreateRunPage.has_user_edited_name) {
      var urlparams = Object.toQueryString();
      new Ajax.Request('/run/suggest_summary', {
        method:'get',
        parameters:{
          plan_id : $('id_plan_id').value,
          product_id : $('id_product_id').value,
          env_id : $('id_env_id').value,
          build_id : $('id_build_id').value
        },
        requestHeaders: {Accept: 'application/json'},
        onSuccess: function(t) {
          obj = jQ.parseJSON(t.responseText);
          $('id_summary').setValue(obj.suggestedSummary);
        },
        // don't worry about failure
      });
    }
  }
};  // end of Nitrate.CreateRunPage

Nitrate.Utils.after_page_load(Nitrate.CreateRunPage.on_load);

