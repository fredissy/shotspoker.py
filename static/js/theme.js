(function() {
    const themes = ['light', 'dark', 'retro', 'windows95'];
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
})();

function toggleTheme() {
    const themes = ['light', 'dark', 'retro', 'windows95'];
    const currentTheme = localStorage.getItem('theme') || 'light';
    const currentIndex = themes.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % themes.length;
    const newTheme = themes[nextIndex];
    
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function applyTheme(theme) {
    const body = document.body;
    
    // Remove existing theme classes
    body.classList.remove('theme-retro', 'theme-windows95');
    document.documentElement.removeAttribute('data-bs-theme');
    
    if (theme === 'retro') {
        body.classList.add('theme-retro');
        // Load retro CSS if not already loaded
        if (!document.querySelector('link[href*="retro.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/retro.css';
            document.head.appendChild(link);
        }
    } else if (theme === 'windows95') {
        body.classList.add('theme-windows95');
        // Load Windows 95/98 CSS if not already loaded
        if (!document.querySelector('link[href*="windows95.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/windows95.css';
            document.head.appendChild(link);
        }
    } else {
        // For light/dark, use Bootstrap's data-bs-theme
        document.documentElement.setAttribute('data-bs-theme', theme);
    }
}
