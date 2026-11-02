document.addEventListener("DOMContentLoaded", function() {
    // Use event delegation for the delete buttons
    document.body.addEventListener('click', function(e) {
        var target = e.target.closest('.delete-module-btn');
        if (target) {
            e.preventDefault();
            
            var deleteUrl = target.getAttribute('data-url');
            var moduleName = target.getAttribute('data-name');
            
            var form = document.getElementById('deleteModuleForm');
            var nameSpan = document.getElementById('modalModuleName');
            
            if (form && nameSpan) {
                form.setAttribute('action', deleteUrl);
                nameSpan.textContent = '📁 ' + moduleName;
                
                // Use jQuery to show the Bootstrap modal
                if (window.jQuery) {
                    window.jQuery('#deleteModuleModal').modal('show');
                }
            }
        }
    });
});