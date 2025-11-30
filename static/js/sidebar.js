(function () {
    'use strict';

    const SIDEBAR_STATE_KEY = 'uams-sidebar-collapsed';
    const SIDEBAR_ID = 'appSidebar';
    const COLLAPSED_CLASS = 'collapsed';
    const BODY_COLLAPSED_CLASS = 'sidebar-collapsed';

    function getSidebarState() {
        try {
            return localStorage.getItem(SIDEBAR_STATE_KEY) === 'true';
        } catch (e) {
            console.error('Error reading sidebar state:', e);
            return false;
        }
    }

    function saveSidebarState(isCollapsed) {
        try {
            localStorage.setItem(SIDEBAR_STATE_KEY, isCollapsed.toString());
        } catch (e) {
            console.error('Error saving sidebar state:', e);
        }
    }

    function setSidebarCollapsed(isCollapsed) {
        const sidebar = document.getElementById(SIDEBAR_ID);
        if (!sidebar) {
            return false;
        }

        sidebar.classList.toggle(COLLAPSED_CLASS, isCollapsed);
        document.body.classList.toggle(BODY_COLLAPSED_CLASS, isCollapsed);
        saveSidebarState(isCollapsed);
        return true;
    }

    function toggleSidebarCollapse() {
        const sidebar = document.getElementById(SIDEBAR_ID);
        if (!sidebar) {
            return;
        }

        const isCollapsed = sidebar.classList.toggle(COLLAPSED_CLASS);
        document.body.classList.toggle(BODY_COLLAPSED_CLASS, isCollapsed);
        saveSidebarState(isCollapsed);

        updateToggleButton(isCollapsed);
    }

    function updateToggleButton(isCollapsed) {
        const toggleBtn = document.getElementById('sidebarCollapseToggle');
        if (!toggleBtn) {
            return;
        }

        const icon = toggleBtn.querySelector('i');
        const label = toggleBtn.querySelector('span');

        if (icon) {
            icon.className = isCollapsed ? 'fa-solid fa-angles-right' : 'fa-solid fa-angles-left';
        }
        if (label) {
            label.textContent = isCollapsed ? 'Expand' : 'Collapse';
        }
        toggleBtn.setAttribute('aria-expanded', (!isCollapsed).toString());
    }

    function applySidebarState() {
        const isCollapsed = getSidebarState();
        if (setSidebarCollapsed(isCollapsed)) {
            updateToggleButton(isCollapsed);
        }
    }

    function ensureToggleButton() {
        let toggleBtn = document.getElementById('sidebarCollapseToggle');
        if (toggleBtn) {
            return toggleBtn;
        }

        const sidebarFooter = document.querySelector('.sidebar-footer');
        if (!sidebarFooter) {
            return null;
        }

        toggleBtn = document.createElement('button');
        toggleBtn.id = 'sidebarCollapseToggle';
        toggleBtn.className = 'btn btn-outline-light btn-sm sidebar-collapse-toggle';
        toggleBtn.type = 'button';
        toggleBtn.setAttribute('aria-expanded', 'true');
        toggleBtn.innerHTML = '<i class="fa-solid fa-angles-left me-2"></i><span>Collapse</span>';

        const themeToggle = document.getElementById('theme-toggle-btn');
        if (themeToggle && themeToggle.parentElement) {
            themeToggle.parentElement.insertBefore(toggleBtn, themeToggle);
        } else {
            sidebarFooter.insertBefore(toggleBtn, sidebarFooter.firstChild);
        }

        return toggleBtn;
    }

    function addSidebarTooltips() {
        const sidebarLinks = document.querySelectorAll('#appSidebar .sidebar-link, #appSidebar .sidebar-sublink');
        sidebarLinks.forEach(function (link) {
            const textContent = link.querySelector('span');
            if (textContent) {
                const text = textContent.textContent.trim();
                if (text) {
                    link.setAttribute('data-tooltip', text);
                }
            }
        });
    }

    function expandActiveSidebarSections() {
        const sidebarNav = document.getElementById('sidebarNav');
        if (!sidebarNav) {
            return;
        }

        const submenus = sidebarNav.querySelectorAll('.sidebar-submenu.collapse');
        submenus.forEach(function (submenu) {
            if (!submenu.id) {
                return;
            }

            const hasActiveLink = submenu.querySelector('.sidebar-sublink.active');
            if (!hasActiveLink) {
                return;
            }

            try {
                if (typeof bootstrap !== 'undefined' && bootstrap.Collapse) {
                    const collapseInstance = bootstrap.Collapse.getOrCreateInstance(submenu, { toggle: false });
                    collapseInstance.show();
                } else {
                    submenu.classList.add('show');
                    submenu.style.height = 'auto';
                }
            } catch (e) {
                console.error('Failed to expand sidebar section:', e);
                submenu.classList.add('show');
            }

            const toggleBtn = sidebarNav.querySelector('[data-bs-target="#' + submenu.id + '"]');
            if (toggleBtn) {
                toggleBtn.classList.add('active');
                toggleBtn.setAttribute('aria-expanded', 'true');
            }
        });
    }

    function initSidebarCollapse() {
        applySidebarState();
        const toggleBtn = ensureToggleButton();

        if (toggleBtn) {
            toggleBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                toggleSidebarCollapse();
            });
        }

        addSidebarTooltips();
        expandActiveSidebarSections();
    }

    window.toggleSidebarCollapse = toggleSidebarCollapse;
    window.getSidebarCollapseState = getSidebarState;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSidebarCollapse);
    } else {
        initSidebarCollapse();
    }
})();

