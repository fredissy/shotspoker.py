(function() {
    const reactionToolbar = document.getElementById('reactionToolbar');
    
    if (!reactionToolbar) return;
    
    reactionToolbar.style.display = 'none';
    
    let toolbarVisible = false;
    
    // Show toolbar when Shift+E is pressed
    document.addEventListener('keydown', function(e) {
        if (e.shiftKey && e.key.toLowerCase() === 'e' && !toolbarVisible) {
            toolbarVisible = true;
            reactionToolbar.style.display = 'block';
            // Small delay to allow CSS transition
            setTimeout(() => {
                reactionToolbar.style.opacity = '0.7';
            }, 10);
        }
    });
    
    // Hide toolbar when either Shift or E is released
    document.addEventListener('keyup', function(e) {
        if ((e.key === 'Shift' || e.key.toLowerCase() === 'e') && toolbarVisible) {
            toolbarVisible = false;
            reactionToolbar.style.opacity = '0';
            // Hide after transition completes
            setTimeout(() => {
                reactionToolbar.style.display = 'none';
            }, 300); // Match CSS transition duration
        }
    });
    
    // Handle edge case: user switches window while holding keys
    window.addEventListener('blur', function() {
        if (toolbarVisible) {
            toolbarVisible = false;
            reactionToolbar.style.opacity = '0';
            setTimeout(() => {
                reactionToolbar.style.display = 'none';
            }, 300);
        }
    });
})();
