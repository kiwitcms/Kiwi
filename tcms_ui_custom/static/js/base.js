document.addEventListener("DOMContentLoaded", function() {
    if (window.jQuery) {
        // Show toasts with a fade-in
        jQuery('.custom-toast').fadeIn(300);

        // Auto-hide after 3 seconds
        setTimeout(function(){
            jQuery('.custom-toast').fadeOut(300);
        }, 3000);

        // Close button functionality
        jQuery('.close-toast').click(function(e){
            e.preventDefault();
            jQuery(this).closest('.custom-toast').fadeOut(200);
        });
    }
});
