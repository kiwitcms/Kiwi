document.addEventListener("DOMContentLoaded", function() {

    // 1. Initialize Select2 for the tags dropdown
    if (window.jQuery && jQuery.fn.select2) {
        jQuery('#id_tags_input').select2({
            placeholder: "Select tags...",
            width: '100%'
        });
    }

    // 2. Handle the "+ Add Step" Button Click
    var addBtn = document.getElementById('add-step-btn');
    if (addBtn) {
        addBtn.addEventListener('click', function(e) {
            e.preventDefault();
            var container = document.getElementById('steps-container');
            var newRow = document.createElement('div');
            newRow.className = 'step-row';
            newRow.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <label style="font-size: 12px;">Step</label>
                        <textarea name="step[]" class="form-control" rows="2"></textarea>
                    </div>
                    <div class="col-md-6">
                        <label style="font-size: 12px;">Expected Result</label>
                        <textarea name="expected[]" class="form-control" rows="2"></textarea>
                    </div>
                </div>`;
            container.appendChild(newRow);
        });
    }
});
