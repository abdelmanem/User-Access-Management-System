/**
 * Theme Switcher for UAMS
 * Handles light/dark mode switching with localStorage persistence
 */

(function() {
    'use strict';

    const THEME_KEY = 'uams-theme';
    const THEME_LIGHT = 'light';
    const THEME_DARK = 'dark';

    /**
     * Get current theme from localStorage or default to light
     */
    function getTheme() {
        try {
            const stored = localStorage.getItem(THEME_KEY);
            if (stored === THEME_DARK || stored === THEME_LIGHT) {
                return stored;
            }
            // Check system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                return THEME_DARK;
            }
        } catch (e) {
            console.error('Error reading theme from localStorage:', e);
        }
        return THEME_LIGHT;
    }

    /**
     * Save theme preference to localStorage
     */
    function saveTheme(theme) {
        try {
            localStorage.setItem(THEME_KEY, theme);
        } catch (e) {
            console.error('Error saving theme to localStorage:', e);
        }
    }

    /**
     * Apply theme to document
     */
    function applyTheme(theme) {
        const html = document.documentElement;
        const body = document.body;
        
        if (theme === THEME_DARK) {
            html.setAttribute('data-theme', 'dark');
            html.classList.add('dark-mode');
            html.classList.remove('light-mode');
            if (body) {
                body.classList.add('dark-mode');
                body.classList.remove('light-mode');
            }
        } else {
            html.setAttribute('data-theme', 'light');
            html.classList.add('light-mode');
            html.classList.remove('dark-mode');
            if (body) {
                body.classList.add('light-mode');
                body.classList.remove('dark-mode');
            }
        }
    }

    /**
     * Update theme toggle button icon and text
     */
    function updateThemeButton(theme) {
        const button = document.getElementById('theme-toggle-btn');
        if (!button) {
            // Button might not be loaded yet, try again after a short delay
            setTimeout(function() {
                updateThemeButton(theme);
            }, 100);
            return;
        }

        const icon = button.querySelector('i');
        const text = button.querySelector('.theme-text');

        if (theme === THEME_DARK) {
            if (icon) {
                icon.className = 'fa-solid fa-sun';
            }
            if (text) {
                text.textContent = 'Light Mode';
            }
            button.setAttribute('title', 'Switch to Light Mode');
        } else {
            if (icon) {
                icon.className = 'fa-solid fa-moon';
            }
            if (text) {
                text.textContent = 'Dark Mode';
            }
            button.setAttribute('title', 'Switch to Dark Mode');
        }
    }

    /**
     * Toggle between light and dark themes
     */
    function toggleTheme() {
        const currentTheme = getTheme();
        const newTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
        saveTheme(newTheme);
        applyTheme(newTheme);
        updateThemeButton(newTheme);
    }

    /**
     * Initialize theme on page load
     */
    function initTheme() {
        const theme = getTheme();
        applyTheme(theme);
        updateThemeButton(theme);

        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            // Use addListener for older browsers, addEventListener for newer ones
            if (mediaQuery.addEventListener) {
                mediaQuery.addEventListener('change', function(e) {
                    // Only auto-switch if user hasn't set a preference
                    if (!localStorage.getItem(THEME_KEY)) {
                        const newTheme = e.matches ? THEME_DARK : THEME_LIGHT;
                        applyTheme(newTheme);
                        updateThemeButton(newTheme);
                    }
                });
            } else if (mediaQuery.addListener) {
                mediaQuery.addListener(function(e) {
                    if (!localStorage.getItem(THEME_KEY)) {
                        const newTheme = e.matches ? THEME_DARK : THEME_LIGHT;
                        applyTheme(newTheme);
                        updateThemeButton(newTheme);
                    }
                });
            }
        }
    }

    // Initialize when DOM is ready
    function setupTheme() {
        initTheme();
        
        // Set up button click handler - use event delegation for reliability
        function attachButtonHandler() {
            const button = document.getElementById('theme-toggle-btn');
            if (button) {
                // Remove any existing handlers
                button.onclick = null;
                const newButton = button.cloneNode(true);
                button.parentNode.replaceChild(newButton, button);
                newButton.id = 'theme-toggle-btn';
                
                // Add multiple event handlers for maximum compatibility
                newButton.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleTheme();
                    return false;
                };
                
                newButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleTheme();
                    return false;
                }, true);
                return true;
            }
            return false;
        }
        
        // Try to attach handler
        if (!attachButtonHandler()) {
            // Button not found, try again after a short delay
            setTimeout(function() {
                if (!attachButtonHandler()) {
                    console.warn('Theme toggle button not found after retry');
                }
            }, 200);
        }
    }

    // Expose toggle function globally immediately
    window.toggleTheme = toggleTheme;
    window.getCurrentTheme = getTheme;
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupTheme);
    } else {
        // DOM already loaded
        setupTheme();
    }
    
    // Also expose on window load as backup
    window.addEventListener('load', function() {
        window.toggleTheme = toggleTheme;
        window.getCurrentTheme = getTheme;
        setupTheme();
    });
    
    // Use event delegation on document as ultimate fallback
    document.addEventListener('click', function(e) {
        if (e.target && (e.target.id === 'theme-toggle-btn' || e.target.closest('#theme-toggle-btn'))) {
            e.preventDefault();
            e.stopPropagation();
            toggleTheme();
            return false;
        }
    }, true);

})();

