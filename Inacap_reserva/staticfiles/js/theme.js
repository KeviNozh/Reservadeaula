// theme.js - Controlador del tema oscuro/claro - Versión simplificada y funcional
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 theme.js cargado - Iniciando gestión de tema...');
    
    // 1. Buscar o crear el botón de cambio de tema
    let themeToggle = document.getElementById('themeToggle');
    
    if (!themeToggle) {
        // Crear botón si no existe
        themeToggle = document.createElement('button');
        themeToggle.id = 'themeToggle';
        themeToggle.type = 'button';
        themeToggle.setAttribute('aria-label', 'Cambiar tema claro/oscuro');
        themeToggle.setAttribute('title', 'Click para cambiar tema');
        themeToggle.style.cssText = `
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        `;
        
        // Agregar al body
        document.body.appendChild(themeToggle);
        console.log('✅ Botón de tema creado e insertado');
    }
    
    // 2. Aplicar tema guardado al cargar
    const savedTheme = localStorage.getItem('theme') || 'light';
    const html = document.documentElement;
    const body = document.body;
    
    if (savedTheme === 'dark') {
        html.setAttribute('data-theme', 'dark');
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
        themeToggle.textContent = '☀️';
        themeToggle.setAttribute('title', 'Cambiar a tema claro');
        console.log('🌙 Tema oscuro aplicado desde localStorage');
    } else {
        html.setAttribute('data-theme', 'light');
        body.classList.remove('dark-theme');
        body.classList.add('light-theme');
        themeToggle.textContent = '🌙';
        themeToggle.setAttribute('title', 'Cambiar a tema oscuro');
        console.log('☀️ Tema claro aplicado desde localStorage');
    }
    
    // 3. Función para cambiar tema
    function toggleTheme() {
        const isDark = body.classList.contains('dark-theme');
        
        if (isDark) {
            // Cambiar a claro
            html.setAttribute('data-theme', 'light');
            body.classList.remove('dark-theme');
            body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
            themeToggle.textContent = '🌙';
            themeToggle.setAttribute('title', 'Cambiar a tema oscuro');
            console.log('🔄 Cambiado a tema claro');
        } else {
            // Cambiar a oscuro
            html.setAttribute('data-theme', 'dark');
            body.classList.add('dark-theme');
            body.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
            themeToggle.textContent = '☀️';
            themeToggle.setAttribute('title', 'Cambiar a tema claro');
            console.log('🔄 Cambiado a tema oscuro');
        }
    }
    
    // 4. Asignar evento al botón
    themeToggle.addEventListener('click', toggleTheme);
    
    // 5. Agregar efecto hover al botón
    themeToggle.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.1)';
        this.style.boxShadow = '0 6px 16px rgba(0,0,0,0.4)';
    });
    
    themeToggle.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
        this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
    });
    
    console.log('✅ theme.js completamente inicializado');
});

// Inicializar también si el DOM ya está cargado
if (document.readyState === 'interactive' || document.readyState === 'complete') {
    document.dispatchEvent(new Event('DOMContentLoaded'));
}