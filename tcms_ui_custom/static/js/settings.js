document.addEventListener("DOMContentLoaded", function() {
    
    // 1. Delete Modal Logic
    document.body.addEventListener('click', function(e) {
        var deleteBtn = e.target.closest('.delete-btn');
        if (deleteBtn) {
            e.preventDefault();
            var url = deleteBtn.getAttribute('data-url');
            var name = deleteBtn.getAttribute('data-name');
            
            document.getElementById('deleteItemForm').setAttribute('action', url);
            document.getElementById('modalItemName').textContent = name;
            
            if (window.jQuery) {
                window.jQuery('#deleteItemModal').modal('show');
            }
        }
    });

    // 2. Inline Edit Toggle Logic
    document.body.addEventListener('click', function(e) {
        // Clicked Edit
        var editBtn = e.target.closest('.edit-btn');
        if (editBtn) {
            e.preventDefault();
            var row = editBtn.closest('tr');
            row.querySelector('.edit-display-mode').style.display = 'none';
            row.querySelector('.edit-edit-mode').style.display = 'block';
            row.querySelector('.item-edit-input').focus();
        }

        // Clicked Cancel
        var cancelBtn = e.target.closest('.cancel-btn');
        if (cancelBtn) {
            e.preventDefault();
            var row = cancelBtn.closest('tr');
            row.querySelector('.edit-display-mode').style.display = 'flex';
            row.querySelector('.edit-edit-mode').style.display = 'none';
        }
    });
});