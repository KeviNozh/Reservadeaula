[file name]: theme.js
[file content begin]
// theme.js - Controlador del tema oscuro/claro - CONTROL EXCLUSIVO POR USUARIO

class ThemeManager {
    constructor() {
        this.darkCss = document.getElementById('darkCss');
        this.darkAdminCss = document.getElementById('darkAdminCss');
        this.themeToggle = null;
        this.init();
    }

    init() {
        // 1. SIEMPRE aplicar el tema guardado por el usuario como prioridad absoluta
        const savedTheme = localStorage.getItem('theme');
        
        // 2. IGNORAR COMPLETAMENTE el tema del sistema al inicio
        if (savedTheme === 'dark') {
            this.enableDarkTheme();
        } else {
            // Si no hay preferencia guardada o es 'light', usar tema claro
            this.disableDarkTheme();
            if (!savedTheme) {
                localStorage.setItem('theme', 'light'); // Guarda la preferencia por defecto
            }
        }

        // 3. Buscar y configurar el toggle del tema
        const existingToggle = document.getElementById('themeToggle') || document.getElementById('themeToggleBtn');
        if (existingToggle) {
            this.themeToggle = existingToggle;
            this.themeToggle.id = this.themeToggle.id || 'themeToggleBtn';
            this.themeToggle.classList.add('theme-toggle-btn');
            this.themeToggle.addEventListener('click', () => this.handleToggleClick());
        } else {
            this.themeToggle = this.createThemeToggle();
            this.addThemeToggleToDOM();
        }

        // 4. Actualizar el estado inicial del toggle
        this.updateToggleState();

        // 5. Aplicar clase al body para facilitar el CSS
        document.addEventListener('DOMContentLoaded', () => {
            this.updateBodyClass();
        });
    }

    createThemeToggle() {
        const toggle = document.createElement('button');
        toggle.id = 'themeToggleBtn';
        toggle.type = 'button';
        toggle.innerHTML = `<span class="theme-icon"></span><span class="theme-text">Tema</span>`;
        toggle.className = 'theme-toggle-btn';
        toggle.setAttribute('aria-label', 'Alternar tema oscuro/claro');
        toggle.setAttribute('title', 'Click para cambiar tema');
        return toggle;
    }

    addThemeToggleToDOM() {
        // Buscar el header para agregar el toggle
        const header = document.querySelector('.header') || document.querySelector('header');
        if (header) {
            // Agregar al final del header
            header.appendChild(this.themeToggle);
        } else {
            // Si no hay header, agregar al body con posición fija
            document.body.appendChild(this.themeToggle);
            this.themeToggle.classList.add('outside-header');
        }

        // Agregar estilos para el botón
        this.addToggleStyles();
        this.themeToggle.addEventListener('click', () => this.handleToggleClick());
        this.updateToggleState();
    }

    handleToggleClick() {
        this.toggleTheme();
    }

    addToggleStyles() {
        const styles = `
            /* Estilos limpios y consistentes para botón de toggle */
            .theme-toggle-btn{
                background: rgba(255,255,255,0.95);
                border: 0;
                padding: 8px 12px;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                color: #111827;
                box-shadow: 0 6px 20px rgba(18, 25, 40, 0.12);
                transition: all 200ms ease;
                z-index: 10000;
                position: relative;
            }
            .theme-toggle-btn:hover{ 
                transform: translateY(-2px); 
                background: rgba(255,255,255,1); 
                box-shadow: 0 8px 25px rgba(18, 25, 40, 0.15);
            }
            .theme-toggle-btn:active{ 
                transform: translateY(0); 
            }
            .theme-toggle-btn .theme-icon{ 
                font-size: 16px;
                transition: transform 300ms ease;
            }
            .theme-toggle-btn .theme-text{ 
                display: none;
                font-weight: 500;
            }
            @media(min-width: 720px){ 
                .theme-toggle-btn .theme-text{ display: inline } 
            }

            /* Botón inyectado por snippet Django */
            #themeToggle{ 
                all: unset; 
                display: inline-block;
                cursor: pointer;
            }

            /* Posicionamiento cuando el botón está fuera del header */
            .theme-toggle-btn.outside-header{ 
                position: fixed; 
                right: 20px; 
                bottom: 20px; 
                z-index: 9999;
                background: rgba(255,255,255,0.95);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            }

            /* Tema oscuro para el propio botón */
            html[data-theme="dark"] .theme-toggle-btn,
            body.dark-theme .theme-toggle-btn { 
                background: rgba(17, 24, 39, 0.95); 
                color: #e6eef8; 
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
            }
            html[data-theme="dark"] .theme-toggle-btn:hover,
            body.dark-theme .theme-toggle-btn:hover { 
                background: rgba(17, 24, 39, 1); 
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
            }
            
            /* Cuando está fuera del header en tema oscuro */
            html[data-theme="dark"] .theme-toggle-btn.outside-header,
            body.dark-theme .theme-toggle-btn.outside-header { 
                background: rgba(17, 24, 39, 0.95); 
                color: #e6eef8; 
                box-shadow: 0 6px 18px rgba(0, 0, 0, 0.4);
            }

            /* Tema claro para el botón */
            html[data-theme="light"] .theme-toggle-btn,
            :not(html[data-theme="dark"]) .theme-toggle-btn:not(.dark-theme) { 
                background: rgba(255, 255, 255, 0.95); 
                color: #111827; 
                box-shadow: 0 6px 20px rgba(18, 25, 40, 0.12);
            }
        `;

        const styleSheet = document.createElement('style');
        styleSheet.id = 'theme-toggle-styles';
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }

    enableDarkTheme() {
        // Habilitar CSS de tema oscuro
        if (this.darkCss) {
            this.darkCss.disabled = false;
        }
        if (this.darkAdminCss) {
            this.darkAdminCss.disabled = false;
        }
        
        // Aplicar clases y atributos
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        document.documentElement.setAttribute('data-theme', 'dark');
        
        // Guardar preferencia
        localStorage.setItem('theme', 'dark');
        
        // Actualizar toggle
        this.updateToggleState();
        
        // Disparar evento personalizado
        this.dispatchThemeChange('dark');
    }

    disableDarkTheme() {
        // Deshabilitar CSS de tema oscuro
        if (this.darkCss) {
            this.darkCss.disabled = true;
        }
        if (this.darkAdminCss) {
            this.darkAdminCss.disabled = true;
        }
        
        // Aplicar clases y atributos
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        document.documentElement.setAttribute('data-theme', 'light');
        
        // Guardar preferencia
        localStorage.setItem('theme', 'light');
        
        // Actualizar toggle
        this.updateToggleState();
        
        // Disparar evento personalizado
        this.dispatchThemeChange('light');
    }

    toggleTheme() {
        const isDark = document.body.classList.contains('dark-theme') || 
                      document.documentElement.getAttribute('data-theme') === 'dark';
        
        if (isDark) {
            this.disableDarkTheme();
        } else {
            this.enableDarkTheme();
        }
        
        // Opcional: recargar solo en desarrollo para aplicar cambios inmediatos
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            setTimeout(() => { 
                console.log('Recargando para aplicar cambios de tema...');
                window.location.reload(); 
            }, 300);
        }
    }

    updateToggleState() {
        if (!this.themeToggle) return;
        
        const isDark = localStorage.getItem('theme') === 'dark' ||
                      document.body.classList.contains('dark-theme') ||
                      document.documentElement.getAttribute('data-theme') === 'dark';
        
        const iconElement = this.themeToggle.querySelector('.theme-icon');
        const textElement = this.themeToggle.querySelector('.theme-text');
        
        if (iconElement) {
            iconElement.textContent = isDark ? '☀️' : '🌙';
            // Animación sutil
            iconElement.style.transform = 'scale(1.2)';
            setTimeout(() => {
                iconElement.style.transform = 'scale(1)';
            }, 200);
        }
        
        if (textElement) {
            textElement.textContent = isDark ? ' Claro' : ' Oscuro';
        }
        
        // Actualizar título del botón
        this.themeToggle.setAttribute('title', isDark ? 
            'Cambiar a tema claro' : 'Cambiar a tema oscuro');
    }

    updateBodyClass() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        if (currentTheme === 'dark') {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }

    dispatchThemeChange(theme) {
        const event = new CustomEvent('themeChanged', {
            detail: { theme: theme }
        });
        window.dispatchEvent(event);
    }

    getCurrentTheme() {
        return localStorage.getItem('theme') || 'light';
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

// Exportar para uso global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}
[file content end]