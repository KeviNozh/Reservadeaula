// theme.js - Controlador del tema oscuro/claro

class ThemeManager {
    constructor() {
        this.darkCss = document.getElementById('darkCss');
        this.themeToggle = this.createThemeToggle();
        this.init();
    }

    init() {
        // Cargar preferencia guardada o usar preferencia del sistema
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
            this.enableDarkTheme();
        } else {
            this.disableDarkTheme();
        }

        // Agregar botón toggle al DOM si no existe
        if (!document.getElementById('themeToggleBtn')) {
            this.addThemeToggleToDOM();
        }

        // Escuchar cambios en la preferencia del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                e.matches ? this.enableDarkTheme() : this.disableDarkTheme();
            }
        });

        // Aplicar clase al body para facilitar el CSS
        document.addEventListener('DOMContentLoaded', () => {
            this.updateBodyClass();
        });
    }

    createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.id = 'themeToggleBtn';
        toggle.innerHTML = `
            <span class="theme-icon">🌙</span>
            <span class="theme-text">Tema</span>
        `;
        toggle.className = 'theme-toggle-btn';
        
        toggle.addEventListener('click', () => {
            this.toggleTheme();
        });

        return toggle;
    }

    addThemeToggleToDOM() {
        // Buscar el header para agregar el toggle
        const header = document.querySelector('.header');
        if (header) {
            // Agregar al final del header
            header.appendChild(this.themeToggle);
        } else {
            // Si no hay header, agregar al body
            document.body.appendChild(this.themeToggle);
        }

        // Agregar estilos para el botón
        this.addToggleStyles();
    }

    addToggleStyles() {
        const styles = `
            .theme-toggle-btn {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 20px;
                padding: 8px 16px;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                transition: all 0.3s ease;
                margin-left: 10px;
            }

            .theme-toggle-btn:hover {
                background: #e5e7eb;
                transform: translateY(-1px);
            }

            .dark-theme .theme-toggle-btn {
                background: #374151;
                border-color: #4b5563;
                color: #e5e7eb;
            }

            .dark-theme .theme-toggle-btn:hover {
                background: #4b5563;
            }

            .theme-toggle-btn .theme-icon {
                font-size: 16px;
            }

            .theme-toggle-btn .theme-text {
                display: none;
            }

            @media (min-width: 768px) {
                .theme-toggle-btn .theme-text {
                    display: inline;
                }
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    enableDarkTheme() {
        if (this.darkCss) {
            this.darkCss.disabled = false;
        }
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        this.updateToggleIcon('☀️');
    }

    disableDarkTheme() {
        if (this.darkCss) {
            this.darkCss.disabled = true;
        }
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        this.updateToggleIcon('🌙');
    }

    toggleTheme() {
        if (document.body.classList.contains('dark-theme')) {
            this.disableDarkTheme();
        } else {
            this.enableDarkTheme();
        }
    }

    updateToggleIcon(icon) {
        const iconElement = this.themeToggle.querySelector('.theme-icon');
        if (iconElement) {
            iconElement.textContent = icon;
        }
    }

    updateBodyClass() {
        if (this.darkCss && !this.darkCss.disabled) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// También inicializar inmediatamente para páginas que ya cargaron
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}