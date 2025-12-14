// theme.js - Controlador del tema oscuro/claro

class ThemeManager {
    constructor() {
        this.darkCss = document.getElementById('darkCss');
        this.themeToggle = null; // se inicializa en init según existencia en el DOM
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

        // Reusar un toggle existente creado por el snippet (_theme_snippet.html)
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
        toggle.innerHTML = `<span class="theme-icon">🌙</span><span class="theme-text">Tema</span>`;
        toggle.className = 'theme-toggle-btn';
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
        this.themeToggle.addEventListener('click', () => this.handleToggleClick());
    }

    handleToggleClick() {
        // Alternar tema sin recargar: aplicar atributo y clase para cubrir ambos snippets/styles
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
                transition: transform 120ms ease, background 160ms ease;
            }
            .theme-toggle-btn:hover{ transform: translateY(-2px); }
            .theme-toggle-btn .theme-icon{ font-size:16px }
            .theme-toggle-btn .theme-text{ display:none }
            @media(min-width:720px){ .theme-toggle-btn .theme-text{ display:inline } }

            /* Si el botón fue inyectado por el snippet (id=themeToggle), unificar apariencia */
            #themeToggle{ all: unset; display:inline-block }

            /* Posicionamiento cuando el botón está fuera del header */
            body .theme-toggle-btn[outside-header]{ position: fixed; right: 18px; bottom: 18px; z-index: 9999 }

            /* Tema oscuro para el propio botón */
            .dark-theme .theme-toggle-btn{ background: rgba(17,24,39,0.9); color: #e6eef8; box-shadow: 0 6px 18px rgba(0,0,0,0.4) }
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
        try{ document.documentElement.setAttribute('data-theme', 'dark'); }catch(e){}
        localStorage.setItem('theme', 'dark');
        this.updateToggleIcon('☀️');
    }

    disableDarkTheme() {
        if (this.darkCss) {
            this.darkCss.disabled = true;
        }
        document.body.classList.remove('dark-theme');
        try{ document.documentElement.removeAttribute('data-theme'); }catch(e){}
        localStorage.setItem('theme', 'light');
        this.updateToggleIcon('🌙');
    }

    // Sincronizar icono/estado del toggle al iniciar
    updateInitialState(){
        const isDark = (localStorage.getItem('theme') === 'dark') || window.matchMedia('(prefers-color-scheme: dark)').matches;
        if(isDark) this.enableDarkTheme(); else this.disableDarkTheme();
    }

    toggleTheme() {
        if (document.body.classList.contains('dark-theme')) {
            this.disableDarkTheme();
        } else {
            this.enableDarkTheme();
        }
    }

    updateToggleIcon(icon) {
        if (!this.themeToggle) return;
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
    // asegurar estado inicial y sincronizar icono
    try{ window.themeManager.updateInitialState(); }catch(e){ }
});

// También inicializar inmediatamente para páginas que ya cargaron
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.themeManager = new ThemeManager();
    });
} else {
    window.themeManager = new ThemeManager();
}