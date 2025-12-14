// theme.js - Versión simplificada y funcional
document.addEventListener('DOMContentLoaded', function() {
    // Buscar botón de tema existente o crear uno
    let themeToggle = document.getElementById('themeToggle') || 
                      document.getElementById('themeToggleBtn') ||
                      document.querySelector('[data-theme-toggle]');
    
    // Si no hay botón, crear uno
    if (!themeToggle) {
        themeToggle = document.createElement('button');
        themeToggle.id = 'themeToggle';
        themeToggle.innerHTML = '🌙';
        themeToggle.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        document.body.appendChild(themeToggle);
    }
    
    // Aplicar tema guardado
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        document.documentElement.setAttribute('data-theme', 'dark');
        themeToggle.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-theme');
        document.documentElement.setAttribute('data-theme', 'light');
        themeToggle.textContent = '🌙';
    }
    
    // Manejar clic en el botón
    themeToggle.addEventListener('click', function() {
        const isDark = document.body.classList.contains('dark-theme');
        
        if (isDark) {
            // Cambiar a claro
            document.body.classList.remove('dark-theme');
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            this.textContent = '🌙';
        } else {
            // Cambiar a oscuro
            document.body.classList.add('dark-theme');
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            this.textContent = '☀️';
        }
    });
});