const themes = ['light', 'dark', 'retro', 'terminal', 'windows95', 'windows311', 'windowsvista', 'dos'];

function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
} else {
    initTheme();
}

function toggleTheme() {
    const themes = ['light', 'dark', 'retro', 'windows95', 'windows311', 'windowsvista', 'dos'];
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
    body.classList.remove('theme-retro', 'theme-windows95', 'theme-windows311', 'theme-windowsvista', 'theme-dos');
    document.documentElement.removeAttribute('data-bs-theme');
    
    if (theme === 'retro') {
        body.classList.add('theme-retro');
        // Load Retro CSS if not already loaded
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
    } else if (theme === 'windows311') {
        body.classList.add('theme-windows311');
        // Load Windows 3.11 CSS if not already loaded
        if (!document.querySelector('link[href*="windows311.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/windows311.css';
            document.head.appendChild(link);
        }
    } else if (theme === 'windowsvista') {
        body.classList.add('theme-windowsvista');
        // Load Windows Vista CSS if not already loaded
        if (!document.querySelector('link[href*="windowsvista.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/windowsvista.css';
            document.head.appendChild(link);
        }
    } else if (theme === 'dos') {
        body.classList.add('theme-dos');
        // Load DOS CSS if not already loaded
        if (!document.querySelector('link[href*="dos.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/static/css/dos.css';
            document.head.appendChild(link);
        }
    } else {
        // For light/dark, use Bootstrap's data-bs-theme
        document.documentElement.setAttribute('data-bs-theme', theme);
    }
}
